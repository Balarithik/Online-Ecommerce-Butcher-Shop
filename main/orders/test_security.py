"""Security and regression tests for customer carts, checkout, and order privacy."""
import json
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from home.models import CustomerProfile
from orders.models import Cart, CartItem, Order, OrderItem
from store.models import Products


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class CustomerOrderSecurityTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user("alice", password="Strong-password-123!")
        self.other = User.objects.create_user("bob", password="Strong-password-123!")
        self.product = Products.objects.create(
            name="Chicken", price=Decimal("200.00"), description="Fresh chicken",
            image1="products_images/chicken.png", is_available=True,
        )
        self.order = Order.objects.create(
            user=self.other, product_id=self.product.pk, product_name=self.product.name,
            name="Bob", mobile="9876543210", location="Bob address",
            quantity=Decimal("1.000"), price=Decimal("200.00"),
        )

    def test_order_history_requires_authentication(self):
        response = self.client.get(reverse("my_orders"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("customer_login"), response.url)

    def test_order_confirmation_is_owner_scoped(self):
        self.client.force_login(self.customer)
        response = self.client.get(reverse("order_confirmation", args=[self.order.pk]))
        self.assertEqual(response.status_code, 404)

    def test_owner_can_view_own_order_confirmation(self):
        self.client.force_login(self.other)
        response = self.client.get(reverse("order_confirmation", args=[self.order.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bob")

    def test_order_history_never_accepts_phone_number_as_an_authentication_factor(self):
        response = self.client.get(reverse("my_orders"), {"mobile": "9876"})
        self.assertEqual(response.status_code, 302)
        self.assertNotContains(response, "Bob address", status_code=302)

    def test_checkout_requires_login(self):
        response = self.client.get(reverse("Checkout_direct", args=[self.product.pk, "1"]))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("customer_login"), response.url)

    def test_cart_add_rejects_invalid_quantities(self):
        self.client.force_login(self.customer)
        for quantity in ("0", "-1", "100.001", "NaN", "Infinity", "not-a-number"):
            response = self.client.post(
                reverse("cart_add_api"),
                data=json.dumps({"product_id": self.product.pk, "qty": quantity}),
                content_type="application/json",
            )
            self.assertEqual(response.status_code, 400, msg=f"quantity={quantity}")
        self.assertFalse(CartItem.objects.exists())

    def test_cart_add_rejects_unavailable_product(self):
        self.product.is_available = False
        self.product.save(update_fields=["is_available"])
        response = self.client.post(
            reverse("cart_add_api"),
            data=json.dumps({"product_id": self.product.pk, "qty": "1"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)

    def test_guest_carts_are_isolated_by_session(self):
        first = self.client
        second = self.client_class()
        first.post(reverse("cart_add_api"), data=json.dumps({
            "product_id": self.product.pk, "qty": "1",
        }), content_type="application/json")
        first_items = first.get(reverse("cart_data_api")).json()["items"]
        second_items = second.get(reverse("cart_data_api")).json()["items"]
        self.assertEqual(len(first_items), 1)
        self.assertEqual(second_items, [])

    def test_customer_cannot_access_another_customers_cart_by_product_id(self):
        own_cart = Cart.objects.create(user=self.customer)
        other_cart = Cart.objects.create(user=self.other)
        CartItem.objects.create(cart=other_cart, product=self.product, quantity=Decimal("2.000"))
        self.client.force_login(self.customer)
        response = self.client.post(
            reverse("cart_remove_api"),
            data=json.dumps({"product_id": self.product.pk}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(CartItem.objects.filter(cart=other_cart, product=self.product).exists())
        self.assertFalse(CartItem.objects.filter(cart=own_cart, product=self.product).exists())

    def test_order_price_is_calculated_from_database_not_posted_price(self):
        self.client.force_login(self.customer)
        with patch("orders.views.send_order_confirmation"):
            response = self.client.post(reverse("Orders", args=[self.product.pk]), {
                "name": "Alice", "mobile": "9876543210",
                "address": "12 Main Street, Uchipuli", "quantity": "2.5",
                "price": "1.00", "order_token": "5f1d6d3e-65c4-4a8a-a1a9-4a33e3b51e91",
            })
        self.assertEqual(response.status_code, 302)
        order = Order.objects.get(user=self.customer)
        self.assertEqual(order.price, Decimal("500.00"))

    def test_checkout_order_token_prevents_duplicate_orders(self):
        self.client.force_login(self.customer)
        payload = {
            "name": "Alice", "mobile": "9876543210",
            "address": "12 Main Street, Uchipuli", "quantity": "1",
            "order_token": "b82a6e61-efb6-4d58-8e42-2e501e7c04c3",
        }
        with patch("orders.views.send_order_confirmation"):
            first = self.client.post(reverse("Orders", args=[self.product.pk]), payload)
            second = self.client.post(reverse("Orders", args=[self.product.pk]), payload)
        self.assertEqual(first.status_code, 302)
        self.assertEqual(second.status_code, 302)
        self.assertEqual(Order.objects.filter(user=self.customer).count(), 1)
        self.assertEqual(OrderItem.objects.filter(order__user=self.customer).count(), 1)

    def test_multi_item_cart_checkout_preserves_every_cart_line(self):
        second_product = Products.objects.create(
            name="Mutton", price=Decimal("600.00"), description="Fresh mutton",
            image1="products_images/mutton.png", is_available=True,
        )
        cart = Cart.objects.create(user=self.customer)
        CartItem.objects.create(cart=cart, product=self.product, quantity=Decimal("1.000"))
        CartItem.objects.create(cart=cart, product=second_product, quantity=Decimal("0.500"))
        self.client.force_login(self.customer)
        with patch("orders.views.send_order_confirmation"):
            response = self.client.post(reverse("Orders", args=[self.product.pk]), {
                "name": "Alice", "mobile": "9876543210",
                "address": "12 Main Street, Uchipuli", "quantity": "1",
                "order_token": "f24b5b52-3d42-46f9-84dd-8ed2d91fd7d2",
            })
        self.assertEqual(response.status_code, 302)
        order = Order.objects.get(user=self.customer)
        self.assertEqual(order.items.count(), 2)
        self.assertEqual(order.price, Decimal("500.00"))

    def test_invalid_gps_pair_is_rejected(self):
        self.client.force_login(self.customer)
        response = self.client.post(reverse("Orders", args=[self.product.pk]), {
            "name": "Alice", "mobile": "9876543210",
            "address": "12 Main Street, Uchipuli", "quantity": "1",
            "latitude": "9.3", "longitude": "",
            "order_token": "ea74a09b-0a4c-49c5-ae2b-6ecb5ad8d3a7",
        })
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Order.objects.filter(user=self.customer).exists())

    def test_confirmation_refresh_does_not_inflate_customer_order_count(self):
        profile = CustomerProfile.objects.create(user=self.other, number_of_orders=1)
        self.client.force_login(self.other)
        url = reverse("order_confirmation", args=[self.order.pk])
        self.client.get(url)
        self.client.get(url)
        profile.refresh_from_db()
        self.assertEqual(profile.number_of_orders, 1)
