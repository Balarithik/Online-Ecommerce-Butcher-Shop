"""Security tests for privileged inventory, image upload, and order operations."""
from io import BytesIO
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from orders.models import Order
from store.models import Products


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class AdminDashboardSecurityTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            "root", "root@example.test", "Strong-admin-password-123!"
        )
        self.customer = User.objects.create_user(
            "customer", password="Strong-customer-password-123!"
        )
        self.product = Products.objects.create(
            name="Chicken", price="200.00", description="Fresh chicken",
            image1="products_images/chicken.png",
        )
        self.order = Order.objects.create(
            user=self.customer, product_id=self.product.pk, product_name=self.product.name,
            name="Customer", mobile="9876543210", location="Address",
            quantity="1.000", price="200.00",
        )

    def _png_upload(self):
        output = BytesIO()
        Image.new("RGB", (2, 2), "white").save(output, format="PNG")
        return SimpleUploadedFile("tiny.png", output.getvalue(), content_type="image/png")

    def test_dashboard_rejects_anonymous_and_regular_users(self):
        url = reverse("admin_dashboard")
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get(url).status_code, 302)

    def test_inventory_mutations_require_superuser(self):
        self.client.force_login(self.customer)
        response = self.client.post(reverse("toggle_product_availability", args=[self.product.pk]))
        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertTrue(self.product.is_available)

    def test_product_deletion_is_post_only(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("delete_product", args=[self.product.pk]))
        self.assertEqual(response.status_code, 405)
        self.assertTrue(Products.objects.filter(pk=self.product.pk).exists())

    def test_order_status_update_rejects_unknown_status(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("update_order", args=[self.order.pk]), {
            "status": "paid_by_attacker",
        })
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "pending")

    def test_admin_login_blocks_protocol_relative_open_redirect(self):
        response = self.client.post(reverse("admin_login"), {
            "username": "root", "password": "Strong-admin-password-123!",
            "next": "//evil.example/phishing",
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("admin_dashboard"))

    @override_settings(CLOUDINARY_UPLOAD_CONFIGURED=False)
    def test_cloudinary_upload_returns_clear_service_unavailable_when_unconfigured(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("upload_product_image"))
        self.assertEqual(response.status_code, 503)
        self.assertIn("not configured", response.json()["error"].lower())

    @override_settings(CLOUDINARY_UPLOAD_CONFIGURED=True)
    def test_cloudinary_upload_rejects_missing_file(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("upload_product_image"))
        self.assertEqual(response.status_code, 400)

    @override_settings(CLOUDINARY_UPLOAD_CONFIGURED=True)
    def test_cloudinary_upload_rejects_non_image_payload(self):
        self.client.force_login(self.admin)
        upload = SimpleUploadedFile("fake.png", b"this is not a png", content_type="image/png")
        response = self.client.post(reverse("upload_product_image"), {"image": upload})
        self.assertEqual(response.status_code, 400)

    @override_settings(CLOUDINARY_UPLOAD_CONFIGURED=True)
    @patch("admin_dashboard.views.cloudinary.uploader.upload")
    def test_cloudinary_upload_uses_random_scoped_public_id_and_https_url(self, upload_mock):
        self.client.force_login(self.admin)
        upload_mock.side_effect = lambda file_obj, public_id, **kwargs: {
            "public_id": public_id,
            "secure_url": "https://res.cloudinary.com/demo/image/upload/" + public_id,
        }
        response = self.client.post(
            reverse("upload_product_image"), {"image": self._png_upload()}
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["public_id"].startswith("products_images/"))
        self.assertTrue(payload["secure_url"].startswith("https://"))
        upload_mock.assert_called_once()

    @override_settings(CLOUDINARY_UPLOAD_CONFIGURED=True)
    @patch("admin_dashboard.views.cloudinary.uploader.upload")
    def test_cloudinary_error_does_not_leak_configured_secret(self, upload_mock):
        from cloudinary.exceptions import Error as CloudinaryError

        secret = "test-secret-do-not-leak"
        upload_mock.side_effect = CloudinaryError("request failed with " + secret)
        self.client.force_login(self.admin)
        with self.settings(CLOUDINARY_API_SECRET=secret, CLOUDINARY_API_KEY="test-key", CLOUDINARY_URL=""):
            response = self.client.post(
                reverse("upload_product_image"), {"image": self._png_upload()}
            )
        self.assertEqual(response.status_code, 502)
        self.assertNotIn(secret, response.content.decode())

    @override_settings(CLOUDINARY_UPLOAD_CONFIGURED=True)
    @patch("admin_dashboard.views.cloudinary.uploader.upload")
    def test_cloudinary_response_with_unexpected_public_id_is_rejected(self, upload_mock):
        self.client.force_login(self.admin)
        upload_mock.return_value = {
            "public_id": "other-folder/forged",
            "secure_url": "https://res.cloudinary.com/demo/image/upload/forged",
        }
        response = self.client.post(
            reverse("upload_product_image"), {"image": self._png_upload()}
        )
        self.assertEqual(response.status_code, 502)
