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

    def test_product_gallery_includes_selectable_images_and_auto_change(self):
        product = Products.objects.create(
            name='Gallery chicken', price='100.00', description='Four images',
            image1='products_images/one.png', image2='products_images/two.png',
            image3='products_images/three.png', image4='products_images/four.png',
        )

        response = self.client.get(reverse('selected_product', args=[product.id]))

        self.assertContains(response, 'id="product-main-image"')
        self.assertContains(response, 'class="product-thumbnail')
        self.assertContains(response, 'restartCarousel()')
        self.assertContains(response, 'data-image-src="/media/products_images/two.png"')
