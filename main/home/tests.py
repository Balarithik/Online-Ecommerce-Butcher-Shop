from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from orders.models import Order
from store.models import Products
from .models import CustomerAddress, CustomerProfile


class CustomerAuthenticationTests(TestCase):
    def test_health_check_reports_main_application_is_alive(self):
        response = self.client.get(reverse('health_check'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok'})
        self.assertEqual(response['Access-Control-Allow-Origin'], '*')
        self.assertIn('no-store', response['Cache-Control'])

    def test_health_check_only_accepts_get_requests(self):
        response = self.client.post(reverse('health_check'))

        self.assertEqual(response.status_code, 405)

    def test_customer_can_sign_up_and_is_logged_in(self):
        response = self.client.post(reverse('customer_signup'), {
            'username': 'customer', 'password1': 'A-strong-password123',
            'password2': 'A-strong-password123',
        })
        self.assertRedirects(response, reverse('home'))
        self.assertTrue(User.objects.filter(username='customer').exists())
        self.assertEqual(str(self.client.get(reverse('home')).wsgi_request.user), 'customer')

    def test_customer_can_log_in(self):
        User.objects.create_user('customer', password='A-strong-password123')
        response = self.client.post(reverse('customer_login'), {
            'username': 'customer', 'password': 'A-strong-password123',
        })
        self.assertRedirects(response, reverse('home'))

    def test_account_dashboard_requires_login(self):
        response = self.client.get(reverse('customer_account'))

        self.assertRedirects(
            response,
            f"{reverse('customer_login')}?next={reverse('customer_account')}",
        )

    def test_customer_can_update_profile_and_manage_saved_addresses(self):
        user = User.objects.create_user('customer', password='A-strong-password123')
        self.client.force_login(user)

        response = self.client.post(reverse('customer_account'), {
            'action': 'update_profile',
            'username': 'asha-kumar',
            'first_name': 'Asha',
            'last_name': 'Kumar',
            'email': 'asha@example.com',
            'mobile': '9876543210',
        })
        self.assertRedirects(response, reverse('customer_account'))
        user.refresh_from_db()
        self.assertEqual(user.username, 'asha-kumar')
        self.assertEqual(user.get_full_name(), 'Asha Kumar')
        self.assertEqual(user.email, 'asha@example.com')
        self.assertEqual(user.customer_profile.mobile, '9876543210')

        response = self.client.post(reverse('customer_account'), {
            'action': 'save_address',
            'label': 'Home',
            'recipient_name': 'Asha Kumar',
            'mobile': '9876543210',
            'address': '12/4, Main Road, Near Bus stand, Uchipuli, PIN: 623534',
        })
        self.assertRedirects(response, reverse('customer_account'))
        address = CustomerAddress.objects.get(user=user)
        self.assertTrue(address.is_default)
        self.assertEqual(address.formatted_address, '12/4, Main Road, Near Bus stand, Uchipuli, PIN: 623534')
        self.assertEqual(self.client.get(reverse('customer_account')).status_code, 200)

        second_response = self.client.post(reverse('customer_account'), {
            'action': 'save_address',
            'label': 'Work',
            'recipient_name': 'Asha Kumar',
            'mobile': '9876543210',
            'address': 'Office, Main Road, Uchipuli',
        })
        self.assertRedirects(second_response, reverse('customer_account'))
        work_address = CustomerAddress.objects.get(user=user, label='Work')
        self.client.post(reverse('customer_account'), {
            'action': 'set_default',
            'address_id': work_address.pk,
        })
        address.refresh_from_db()
        work_address.refresh_from_db()
        self.assertFalse(address.is_default)
        self.assertTrue(work_address.is_default)

        self.client.post(reverse('customer_account'), {
            'action': 'delete_address',
            'address_id': work_address.pk,
        })
        address.refresh_from_db()
        self.assertTrue(address.is_default)

    def test_customer_cannot_edit_another_users_address(self):
        user = User.objects.create_user('customer', password='A-strong-password123')
        other_user = User.objects.create_user('other', password='A-strong-password123')
        address = CustomerAddress.objects.create(
            user=other_user,
            recipient_name='Other customer',
            mobile='9876543210',
            address='1, Main Road, Uchipuli',
        )
        self.client.force_login(user)

        response = self.client.get(reverse('customer_account'), {'edit_address': address.pk})

        self.assertEqual(response.status_code, 404)

    def test_customer_can_delete_account_without_deleting_order_history(self):
        user = User.objects.create_user('customer', password='A-strong-password123')
        self.client.force_login(user)
        CustomerProfile.objects.create(user=user, mobile='9876543210')
        CustomerAddress.objects.create(
            user=user,
            recipient_name='Customer',
            mobile='9876543210',
            address='1, Main Road, Uchipuli',
            is_default=True,
        )
        order = Order.objects.create(
            user=user,
            product_name='Test product',
            name='Customer',
            mobile='9876543210',
            price='100.00',
            location='1, Main Road, Uchipuli',
        )

        response = self.client.post(reverse('delete_customer_account'))

        self.assertRedirects(response, reverse('home'))
        self.assertFalse(User.objects.filter(pk=user.pk).exists())
        self.assertFalse(CustomerAddress.objects.filter(user_id=user.pk).exists())
        order.refresh_from_db()
        self.assertIsNone(order.user_id)
        self.assertEqual(order.name, 'Deleted customer')
        self.assertIsNone(order.mobile)
        self.assertEqual(order.location, '')


class HomeProductNavigationTests(TestCase):
    def test_home_buy_now_opens_the_selected_product_page(self):
        product = Products.objects.create(
            name='Fresh Chicken',
            price=200,
            description='Cut fresh to order',
            image1='products_images/test.png',
        )
        response = self.client.get(reverse('home'))
        target = reverse('selected_product', kwargs={'product_id': product.id})
        page_html = response.content.decode()
        buy_now_position = page_html.index('Buy Now')
        buy_now_link_start = page_html.rfind('<a', 0, buy_now_position)
        buy_now_link_end = page_html.find('</a>', buy_now_position)

        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(buy_now_link_start, 0)
        self.assertGreater(buy_now_link_end, buy_now_link_start)
        self.assertIn(f'href="{target}"', page_html[buy_now_link_start:buy_now_link_end])
