from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model


class AdminEndpointTests(TestCase):
    def test_delete_endpoint_rejects_get(self):
        user = get_user_model().objects.create_superuser('admin', 'admin@example.com', 'test-password')
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse('delete_product', args=[999])).status_code, 405)
