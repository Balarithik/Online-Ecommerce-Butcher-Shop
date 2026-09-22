from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


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
