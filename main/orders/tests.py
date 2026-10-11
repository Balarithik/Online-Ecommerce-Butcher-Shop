import re
from unittest.mock import patch

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from store.models import Products
from orders.models import Cart, CartItem, Order
from orders.forms import OrderForm
from orders.notifications import send_order_confirmation
from home.models import CustomerAddress
from decimal import Decimal

@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class OrderTestCase(TestCase):
    def setUp(self):
        # Create a test product
        self.product = Products.objects.create(
            name="Test Chicken",
            price=200.0,
            description="Fresh test poultry",
            image1="products_images/test.png"
        )
        
        # Create users
        self.superuser = User.objects.create_superuser(
            username="admin",
            password="adminpassword",
            email="admin@test.com"
        )
        self.normal_user = User.objects.create_user(
            username="normal",
            password="userpassword",
            email="user@test.com"
        )

    def test_order_form_valid(self):
        # Test OrderForm validation
        data = {
            'name': 'Test User',
            'mobile': '9876543210',
            'address': '123 Test Street, Test City',
            'instructions': 'Leave at door',
            'quantity': 2.5
        }
        form = OrderForm(data=data)
        self.assertTrue(form.is_valid())

    def test_order_form_invalid(self):
        # Test form validation with missing required fields
        data = {
            'name': '',
            'mobile': '',
            'address': '',
            'quantity': ''
        }
        form = OrderForm(data=data)
        self.assertFalse(form.is_valid())

    def test_authenticated_customer_can_view_orders(self):
        self.client.force_login(self.normal_user)

        response = self.client.get(reverse('my_orders'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Lakshmi Broliers Order Center')

    def test_checkout_uses_saved_account_address_without_manual_entry(self):
        self.normal_user.first_name = 'Normal Customer'
        self.normal_user.save()
        address = CustomerAddress.objects.create(
            user=self.normal_user,
            label='Home',
            recipient_name='Delivery Recipient',
            mobile='9876543210',
            address='12/4, Main Road, Uchipuli',
            is_default=True,
        )
        self.client.force_login(self.normal_user)

        response = self.client.get(reverse('Checkout_direct', args=[self.product.id, '1']))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Choose a saved delivery address')
        self.assertContains(response, 'Delivery Recipient')
        self.assertContains(response, address.formatted_address)
        self.assertNotContains(response, 'id="addr_house"')

    def test_order_uses_selected_saved_address_instead_of_forged_checkout_values(self):
        address = CustomerAddress.objects.create(
            user=self.normal_user,
            label='Home',
            recipient_name='Saved Recipient',
            mobile='9876543210',
            address='12/4, Saved Street, Uchipuli',
            is_default=True,
        )
        self.client.force_login(self.normal_user)

        response = self.client.post(reverse('Orders', kwargs={'product_id': self.product.id}), {
            'saved_address_id': address.pk,
            'name': 'Forged Name',
            'mobile': '1111111111',
            'address': 'Forged Address',
            'quantity': '1',
        })

        self.assertEqual(response.status_code, 200)
        order = Order.objects.get()
        self.assertEqual(order.user, self.normal_user)
        self.assertEqual(order.name, 'Saved Recipient')
        self.assertEqual(order.mobile, '9876543210')
        self.assertEqual(order.location, address.formatted_address)

    def test_order_price_tamper_prevention(self):
        # Test server-side price calculation and tamper prevention
        client = Client()
        client.force_login(self.normal_user)
        post_data = {
            'name': 'Bala Test',
            'mobile': '7397511387',
            'address': '9/427 Kamarajar Nagar, Uchipuli',
            'instructions': 'None',
            'quantity': '2.5',
            'price': '10.0'  # Try to set a fake low price of ₹10
        }
        url = reverse('Orders', kwargs={'product_id': self.product.id})
        response = client.post(url, post_data)
        
        self.assertEqual(response.status_code, 200) # Order placement successful
        # Verify the saved price is calculated server-side: 200.0 * 2.5 = 500.0 (not 10.0)
        order = Order.objects.latest('order_id')
        self.assertEqual(order.price, Decimal('500.00'))
        self.assertEqual(order.product_name, "Test Chicken")

    def test_order_saves_customer_shared_gps_location(self):
        client = Client()
        client.force_login(self.normal_user)
        response = client.post(reverse('Orders', kwargs={'product_id': self.product.id}), {
            'name': 'Bala Test',
            'mobile': '7397511387',
            'address': '9/427 Kamarajar Nagar, Uchipuli',
            'quantity': '0.25',
            'latitude': '9.310044',
            'longitude': '78.994671',
        })
        self.assertEqual(response.status_code, 200)
        order = Order.objects.latest('order_id')
        self.assertEqual(order.latitude, Decimal('9.310044'))
        self.assertEqual(order.longitude, Decimal('78.994671'))
        self.assertContains(response, 'Open shared GPS pin in Maps')

    def test_order_rejects_invalid_gps_coordinates(self):
        client = Client()
        client.force_login(self.normal_user)
        response = client.post(reverse('Orders', kwargs={'product_id': self.product.id}), {
            'name': 'Bala Test',
            'mobile': '7397511387',
            'address': 'Test address',
            'quantity': '1',
            'latitude': '91',
            'longitude': '78.994671',
        })
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Order.objects.exists())

    def test_admin_permissions_superuser_only(self):
        # Test that administrative views are restricted to superusers only
        client = Client()
        dashboard_url = reverse('admin_dashboard')
        add_product_url = reverse('add_product_modal')
        
        # 1. Anonymous user redirected
        response = client.get(dashboard_url)
        self.assertRedirects(response, f"/admin_login/?next={dashboard_url}")
        
        # 2. Normal logged-in user redirected
        client.login(username="normal", password="userpassword")
        response = client.get(dashboard_url)
        self.assertRedirects(response, f"/admin_login/?next={dashboard_url}")
        
        response = client.get(add_product_url)
        self.assertRedirects(response, f"/admin_login/?next={add_product_url}")
        
        # 3. Superuser is allowed
        client.login(username="admin", password="adminpassword")
        response = client.get(dashboard_url)
        self.assertEqual(response.status_code, 200)

    def test_negative_quantity_is_rejected(self):
        client = Client()
        client.force_login(self.normal_user)
        response = client.post(reverse('Orders', kwargs={'product_id': self.product.id}), {
            'name': 'Bala Test', 'mobile': '7397511387', 'address': 'Test address', 'quantity': '-1',
        })
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Order.objects.exists())

    def test_unavailable_product_cannot_be_ordered(self):
        self.product.is_available = False
        self.product.save()
        client = Client()
        client.force_login(self.normal_user)
        response = client.post(reverse('Orders', kwargs={'product_id': self.product.id}), {
            'name': 'Bala Test', 'mobile': '7397511387', 'address': 'Test address', 'quantity': '1',
        })
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Order.objects.exists())

    def test_order_total_remains_historical_after_price_change(self):
        client = Client()
        client.force_login(self.normal_user)
        client.post(reverse('Orders', kwargs={'product_id': self.product.id}), {
            'name': 'Bala Test', 'mobile': '7397511387', 'address': 'Test address', 'quantity': '1',
        })
        self.product.price = Decimal('300.00')
        self.product.save()
        self.assertEqual(Order.objects.get().price, Decimal('200.00'))

    def test_order_routes_require_sign_in_and_preserve_checkout_destination(self):
        checkout_url = reverse('Checkout_direct', args=[self.product.id, '1'])

        checkout_response = self.client.get(checkout_url)
        order_response = self.client.post(reverse('Orders', args=[self.product.id]), {
            'quantity': '1',
        })

        self.assertRedirects(checkout_response, f"{reverse('customer_login')}?next={checkout_url}")
        self.assertRedirects(order_response, f"{reverse('customer_login')}?next={checkout_url}")
        self.assertFalse(Order.objects.exists())

    def test_cart_is_isolated_between_authenticated_customers(self):
        other_user = User.objects.create_user('other', password='userpassword')
        other_client = Client()
        self.client.force_login(self.normal_user)
        other_client.force_login(other_user)

        self.client.post(reverse('cart_add_api'), {'product_id': self.product.id, 'qty': '1'})
        other_cart = other_client.get(reverse('cart_data_api')).json()

        self.assertEqual(Cart.objects.filter(user=self.normal_user).count(), 1)
        self.assertEqual(Cart.objects.filter(user=other_user).count(), 1)
        self.assertEqual(other_cart['items'], [])

    def test_guest_cart_merges_into_account_cart_after_login(self):
        guest_client = Client()
        guest_client.post(reverse('cart_add_api'), {'product_id': self.product.id, 'qty': '0.500'})
        guest_cart = Cart.objects.get(user__isnull=True)

        response = guest_client.post(reverse('customer_login'), {
            'username': 'normal',
            'password': 'userpassword',
            'next': reverse('cart'),
        })

        self.assertRedirects(response, reverse('cart'))
        customer_cart = Cart.objects.get(user=self.normal_user)
        self.assertEqual(CartItem.objects.get(cart=customer_cart, product=self.product).quantity, Decimal('0.500'))
        self.assertFalse(Cart.objects.filter(pk=guest_cart.pk).exists())

    def test_checkout_token_prevents_duplicate_orders(self):
        self.client.force_login(self.normal_user)
        checkout = self.client.get(reverse('Checkout_direct', args=[self.product.id, '1']))
        token_match = re.search(r'name="order_token" value="([^"]+)"', checkout.content.decode())
        self.assertIsNotNone(token_match)
        order_data = {
            'order_token': token_match.group(1),
            'name': 'Test User',
            'mobile': '9876543210',
            'address': '1 Test Street, Uchipuli',
            'quantity': '1',
        }

        first = self.client.post(reverse('Orders', args=[self.product.id]), order_data)
        second = self.client.post(reverse('Orders', args=[self.product.id]), order_data)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(Order.objects.filter(user=self.normal_user).count(), 1)

    def test_admin_status_update_changes_the_existing_order_only(self):
        order = Order.objects.create(
            user=self.normal_user,
            product_name=self.product.name,
            product_id=self.product.id,
            name='Test User',
            mobile='9876543210',
            location='1 Test Street, Uchipuli',
            quantity='1',
            price='200.00',
        )
        self.client.force_login(self.superuser)

        response = self.client.post(reverse('update_order', args=[order.order_id]), {'status': 'delivered'})

        self.assertRedirects(response, reverse('admin_orders'))
        order.refresh_from_db()
        self.assertEqual(order.status, 'delivered')
        self.assertEqual(Order.objects.count(), 1)

    @override_settings(
        TWILIO_ACCOUNT_SID='ACtest',
        TWILIO_AUTH_TOKEN='test-token',
        TWILIO_SMS_FROM='+15550000000',
        TWILIO_WHATSAPP_FROM='whatsapp:+14155238886',
        ORDER_NOTIFICATION_COUNTRY_CODE='91',
    )
    @patch('orders.notifications.requests.post')
    def test_order_confirmation_sends_sms_and_whatsapp(self, post):
        post.return_value.raise_for_status.return_value = None
        order = Order.objects.create(
            user=self.normal_user,
            product_name=self.product.name,
            product_id=self.product.id,
            name='Test User',
            mobile='9876543210',
            location='1 Test Street, Uchipuli',
            quantity='1',
            price='200.00',
        )

        results = send_order_confirmation(order)

        self.assertEqual(results, {'sms': True, 'whatsapp': True})
        self.assertEqual(post.call_count, 2)
        self.assertEqual(post.call_args_list[0].kwargs['data']['To'], '+919876543210')
        self.assertEqual(post.call_args_list[1].kwargs['data']['To'], 'whatsapp:+919876543210')
