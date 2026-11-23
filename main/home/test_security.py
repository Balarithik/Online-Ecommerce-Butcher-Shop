"""Security tests for account redirects, address ownership, and account deletion."""
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from home.models import CustomerAddress
from orders.models import Order


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class CustomerAccountSecurityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("alice", password="Strong-password-123!")
        self.other = User.objects.create_user("bob", password="Strong-password-123!")

    def test_login_rejects_external_redirect(self):
        response = self.client.post(reverse("customer_login"), {
            "username": "alice", "password": "Strong-password-123!",
            "next": "https://evil.example/",
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("home"))

    def test_signup_rejects_protocol_relative_redirect(self):
        response = self.client.post(reverse("customer_signup"), {
            "username": "new-customer",
            "password1": "Strong-password-123!",
            "password2": "Strong-password-123!",
            "next": "//evil.example/",
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("home"))

    def test_customer_cannot_change_another_users_default_address(self):
        address = CustomerAddress.objects.create(
            user=self.other, recipient_name="Bob", mobile="9876543210",
            address="1 Main Street, Uchipuli", is_default=True,
        )
        self.client.force_login(self.user)
        response = self.client.post(reverse("customer_account"), {
            "action": "set_default", "address_id": address.pk,
        })
        self.assertEqual(response.status_code, 404)
        address.refresh_from_db()
        self.assertTrue(address.is_default)

    def test_customer_cannot_delete_another_users_address(self):
        address = CustomerAddress.objects.create(
            user=self.other, recipient_name="Bob", mobile="9876543210",
            address="1 Main Street, Uchipuli", is_default=True,
        )
        self.client.force_login(self.user)
        response = self.client.post(reverse("customer_account"), {
            "action": "delete_address", "address_id": address.pk,
        })
        self.assertEqual(response.status_code, 404)
        self.assertTrue(CustomerAddress.objects.filter(pk=address.pk).exists())

    def test_account_deletion_is_post_only(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("delete_customer_account"))
        self.assertEqual(response.status_code, 405)
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())

    def test_account_deletion_preserves_orders_but_anonymizes_customer_details(self):
        order = Order.objects.create(
            user=self.user, product_name="Chicken", name="Alice", mobile="9876543210",
            location="Private address", quantity="1.000", price="200.00",
        )
        self.client.force_login(self.user)
        response = self.client.post(reverse("delete_customer_account"))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(pk=self.user.pk).exists())
        order.refresh_from_db()
        self.assertIsNone(order.user_id)
        self.assertEqual(order.name, "Deleted customer")
        self.assertIsNone(order.mobile)
        self.assertEqual(order.location, "")
