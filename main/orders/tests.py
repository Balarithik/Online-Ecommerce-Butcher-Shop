from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from store.models import Products
from orders.models import Order
from orders.forms import OrderForm
from decimal import Decimal

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

    def test_order_price_tamper_prevention(self):
        # Test server-side price calculation and tamper prevention
        client = Client()
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
        response = Client().post(reverse('Orders', kwargs={'product_id': self.product.id}), {
            'name': 'Bala Test', 'mobile': '7397511387', 'address': 'Test address', 'quantity': '-1',
        })
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Order.objects.exists())

    def test_unavailable_product_cannot_be_ordered(self):
        self.product.is_available = False
        self.product.save()
        response = Client().post(reverse('Orders', kwargs={'product_id': self.product.id}), {
            'name': 'Bala Test', 'mobile': '7397511387', 'address': 'Test address', 'quantity': '1',
        })
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Order.objects.exists())

    def test_order_total_remains_historical_after_price_change(self):
        Client().post(reverse('Orders', kwargs={'product_id': self.product.id}), {
            'name': 'Bala Test', 'mobile': '7397511387', 'address': 'Test address', 'quantity': '1',
        })
        self.product.price = Decimal('300.00')
        self.product.save()
        self.assertEqual(Order.objects.get().price, Decimal('200.00'))
