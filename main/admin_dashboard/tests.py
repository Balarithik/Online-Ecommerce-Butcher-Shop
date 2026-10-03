import re

from django.test import Client
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse
from django.conf import settings
from django.contrib.auth import get_user_model
from store.models import Products
from orders.models import Order


class AdminEndpointTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            'admin-ui-test',
            'admin-ui@example.com',
            'test-password',
        )
        self.client.force_login(self.admin)

    def test_delete_endpoint_rejects_get(self):
        self.assertEqual(self.client.get(reverse('delete_product', args=[999])).status_code, 405)

    def test_dashboard_and_inventory_render_responsive_navigation_and_cards(self):
        Products.objects.create(
            name='Test Poultry Cut',
            price=250,
            description='Freshly cut to order',
            image1='products_images/test.png',
        )
        Order.objects.create(
            product_id=1,
            product_name='Test Poultry Cut',
            name='Test Customer',
            mobile='9876543210',
            quantity='0.250',
            price='62.50',
            location='Uchipuli Main Road',
            latitude='9.310044',
            longitude='78.994671',
        )

        dashboard = self.client.get(reverse('admin_dashboard'))
        inventory = self.client.get(reverse('admin_products'))

        self.assertEqual(dashboard.status_code, 200)
        self.assertContains(dashboard, 'id="mobileMenuBtn"')
        self.assertContains(dashboard, 'id="mobileSidebarBackdrop"')
        self.assertContains(dashboard, 'class="space-y-3 p-3 md:hidden"')
        self.assertContains(dashboard, 'Manage Order')
        self.assertContains(dashboard, 'Open shared GPS pin')
        self.assertEqual(inventory.status_code, 200)
        self.assertContains(inventory, 'Test Poultry Cut')
        self.assertContains(inventory, 'md:hidden')
        self.assertContains(inventory, 'Mark Out of Stock')

    def test_orders_page_renders_mobile_order_cards(self):
        Order.objects.create(
            product_id=1,
            product_name='Fresh Chicken',
            name='Test Customer',
            mobile='9876543210',
            quantity='0.250',
            price='62.50',
            location='Uchipuli Main Road',
            latitude='9.310044',
            longitude='78.994671',
        )

        response = self.client.get(reverse('admin_orders'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="space-y-3 md:hidden"')
        self.assertContains(response, 'Manage Order')
        self.assertContains(response, 'Open shared GPS pin')
        self.assertContains(response, 'Uchipuli Main Road')

    def test_customers_page_renders_responsive_customers_and_order_counts(self):
        customer = get_user_model().objects.create_user(
            username='shop-customer',
            email='customer@example.com',
            first_name='Lakshmi',
            last_name='Customer',
        )
        Order.objects.create(
            user=customer,
            product_name='Fresh Chicken',
            name='Lakshmi Customer',
            mobile='9876543210',
            quantity='0.250',
            price='62.50',
        )

        response = self.client.get(reverse('admin_customers'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Registered Customers')
        self.assertContains(response, 'class="space-y-3 md:hidden"')
        self.assertContains(response, 'Lakshmi Customer')
        self.assertContains(response, 'customer@example.com')
        self.assertContains(response, '1 order')
        self.assertContains(response, 'Orders')

    def test_customers_page_search_returns_empty_state(self):
        response = self.client.get(reverse('admin_customers'), {'q': 'missing-customer'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No customers match your search.')
        self.assertContains(response, 'Matching customers')

    def test_order_management_modal_uses_responsive_theme_styles(self):
        order = Order.objects.create(
            product_id=1,
            product_name='Fresh Chicken',
            name='Test Customer',
            mobile='9876543210',
            quantity='0.250',
            price='62.50',
            location='Uchipuli Main Road',
            latitude='9.310044',
            longitude='78.994671',
        )

        response = self.client.get(reverse('update_order', args=[order.order_id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'role="dialog"')
        self.assertContains(response, 'max-h-[92vh]')
        self.assertContains(response, 'Open shared GPS pin in Maps')
        self.assertNotContains(response, 'px-lg')
        self.assertNotContains(response, 'font-headline-md')

    def test_admin_login_is_a_standalone_branded_page(self):
        response = self.client.get(reverse('admin_login'), {'next': '/admin_dashboard/'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Lakshmi Broliers')
        self.assertContains(response, 'name="next" value="/admin_dashboard/"')
        self.assertContains(response, 'id="togglePassword"')
        self.assertNotContains(response, 'id="adminSidebar"')
        self.assertEqual(response.content.decode().count('<main'), 1)

    def test_admin_login_displays_invalid_credentials_message(self):
        response = self.client.post(reverse('admin_login'), {
            'username': self.admin.username,
            'password': 'incorrect-password',
            'next': '/admin_dashboard/',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid credentials or not an administrator.')
    def test_admin_login_sets_csrf_cookie_and_accepts_matching_form_token(self):
        csrf_client = Client(enforce_csrf_checks=True)
        login_page = csrf_client.get(reverse('admin_login'), {'next': '/admin_dashboard/'})
        response_html = login_page.content.decode()
        csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', response_html)

        self.assertIsNotNone(csrf_match)
        self.assertIn('csrftoken', csrf_client.cookies)
        self.assertIn('no-store', login_page['Cache-Control'])

        rejected = csrf_client.post(reverse('admin_login'), {
            'username': 'invalid-admin',
            'password': 'invalid-password',
        })
        self.assertEqual(rejected.status_code, 403)

        response = csrf_client.post(reverse('admin_login'), {
            'csrfmiddlewaretoken': csrf_match.group(1),
            'username': 'invalid-admin',
            'password': 'invalid-password',
            'next': '/admin_dashboard/',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid credentials or not an administrator.')
        self.assertContains(response, 'name="next" value="/admin_dashboard/"')

    def test_add_product_modal_uses_responsive_theme_layout(self):
        response = self.client.get(reverse('add_product_modal'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'role="dialog"')
        self.assertContains(response, 'max-h-[92vh]')
        self.assertContains(response, 'Main Image (Required)')
        self.assertContains(response, 'Image 2 (Optional)')
        self.assertContains(response, 'CLOUDINARY_UPLOAD_PRESET')
        self.assertContains(response, 'data-cloudinary-upload')
        self.assertNotContains(response, 'p-xl')
        self.assertNotContains(response, 'font-headline-lg')

    @override_settings(
        CLOUDINARY_UPLOAD_CONFIGURED=True,
        CLOUDINARY_CLOUD_NAME='test-cloud',
        CLOUDINARY_UPLOAD_PRESET='test-unsigned-preset',
    )
    def test_add_product_saves_unsigned_cloudinary_public_ids(self):
        response = self.client.post(reverse('add_product_modal'), {
            'name': 'Unsigned Cloudinary Chicken',
            'price': '275.00',
            'description': 'Freshly cut to order',
            'is_available': 'on',
            'image1_public_id': 'products_images/main-image',
            'image2_public_id': 'products_images/side-image',
        })

        self.assertEqual(response.status_code, 302)
        product = Products.objects.get(name='Unsigned Cloudinary Chicken')
        self.assertEqual(product.image1.name, 'products_images/main-image')
        self.assertEqual(product.image2.name, 'products_images/side-image')

    @override_settings(
        CLOUDINARY_UPLOAD_CONFIGURED=True,
        CLOUDINARY_CLOUD_NAME='test-cloud',
        CLOUDINARY_UPLOAD_PRESET='test-unsigned-preset',
    )
    def test_add_product_rejects_public_ids_outside_product_folder(self):
        response = self.client.post(reverse('add_product_modal'), {
            'name': 'Invalid Cloudinary Image',
            'price': '275.00',
            'description': 'Freshly cut to order',
            'is_available': 'on',
            'image1_public_id': 'other-folder/not-allowed',
        })

        self.assertEqual(response.status_code, 400)
        self.assertFalse(Products.objects.filter(name='Invalid Cloudinary Image').exists())

    @override_settings(
        CLOUDINARY_UPLOAD_CONFIGURED=True,
        CLOUDINARY_CLOUD_NAME='test-cloud',
        CLOUDINARY_UPLOAD_PRESET='test-unsigned-preset',
    )
    def test_edit_product_replaces_unsigned_image_without_server_upload(self):
        product = Products.objects.create(
            name='Existing Chicken',
            price='250.00',
            description='Existing description',
            image1='products_images/old-image',
        )

        response = self.client.post(reverse('edit_product_modal', args=[product.id]), {
            'name': 'Updated Chicken',
            'price': '275.00',
            'description': 'Updated description',
            'is_available': 'on',
            'image1_public_id': 'products_images/new-image',
        })

        self.assertEqual(response.status_code, 302)
        product.refresh_from_db()
        self.assertEqual(product.name, 'Updated Chicken')
        self.assertEqual(product.image1.name, 'products_images/new-image')

    @override_settings(CLOUDINARY_UPLOAD_CONFIGURED=False)
    def test_product_upload_is_blocked_until_unsigned_preset_is_configured(self):
        response = self.client.post(reverse('add_product_modal'), {})

        self.assertEqual(response.status_code, 503)
        self.assertContains(response, 'CLOUDINARY_UPLOAD_PRESET', status_code=503)

    def test_cloudinary_storage_uses_configured_cloud_or_local_fallback(self):
        if settings.CLOUDINARY_CLOUD_NAME:
            self.assertEqual(
                settings.STORAGES['default']['BACKEND'],
                'cloudinary_storage.storage.MediaCloudinaryStorage',
            )
            self.assertIn('CLOUD_NAME', settings.CLOUDINARY_STORAGE)
            self.assertTrue(settings.CLOUDINARY_STORAGE['SECURE'])
        else:
            self.assertEqual(
                settings.STORAGES['default']['BACKEND'],
                'django.core.files.storage.FileSystemStorage',
            )
