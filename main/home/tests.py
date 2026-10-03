from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from store.models import Products


class CustomerAuthenticationTests(TestCase):
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
