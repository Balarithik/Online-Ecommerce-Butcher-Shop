from django.test import TestCase
from django.urls import reverse

from store.models import Products


class AvailabilityTests(TestCase):
    def test_unavailable_product_is_not_publicly_accessible(self):
        product = Products.objects.create(
            name='Unavailable chicken', price='100.00', description='Not for sale',
            image1='products_images/test.png', is_available=False,
        )
        self.assertEqual(self.client.get(reverse('selected_product', args=[product.id])).status_code, 404)
