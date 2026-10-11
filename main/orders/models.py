from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from decimal import Decimal
import uuid

# Create your models here.

class Order(models.Model):
    status_choices = [
        ('pending', 'Pending'),
        ('preparing', 'Preparing'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled')
    ]

    order_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    product_id = models.IntegerField(null=True, blank=True)
    product_name = models.CharField(max_length=100, null=True)
    name = models.CharField(max_length=100)
    mobile = models.CharField(max_length=15, null=True, blank=True)
    quantity = models.DecimalField(max_digits=6, decimal_places=3, default=Decimal('1.000'), validators=[MinValueValidator(Decimal('0.250')), MaxValueValidator(Decimal('100.000'))])
    # This is the order-line total at purchase time, not the product's live price.
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    location = models.CharField(max_length=500, null=True, blank=True)
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('-90')), MaxValueValidator(Decimal('90'))],
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('-180')), MaxValueValidator(Decimal('180'))],
    )
    instructions = models.TextField(null=True, blank=True)
    delivery_slot = models.CharField(max_length=100, default='Express Delivery (45-60 Mins)', null=True, blank=True)
    cut_preference = models.CharField(max_length=100, default='Curry Cut (Medium)', null=True, blank=True)
    payment_method = models.CharField(max_length=50, default='Cash on Delivery')
    status = models.CharField(max_length=30, choices=status_choices, default='pending')
    # A checkout form submits this opaque value so a refresh/double-click cannot
    # turn one purchase into multiple order rows.
    placement_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def get_items(self):
        items = list(self.items.select_related('product').all())
        if items:
            return items
        if self.product_name:
            return [{
                'product_name': self.product_name,
                'quantity': self.quantity,
                'price': self.price,
                'cut_preference': self.cut_preference,
                'product': None
            }]
        return []

    def __str__(self):
        return f"Order #{self.order_id} - {self.name} ({self.product_name or 'Items'})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('store.Products', on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=100)
    quantity = models.DecimalField(max_digits=6, decimal_places=3, default=Decimal('1.000'))
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cut_preference = models.CharField(max_length=100, default='Curry Cut (Medium)')

    def __str__(self):
        return f"{self.quantity}kg x {self.product_name} (Order #{self.order.order_id})"


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='cart')
    session_key = models.CharField(max_length=40, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def total_price(self):
        return sum((item.subtotal for item in self.items.select_related('product').all()), Decimal('0.00'))

    def item_count(self):
        return sum(int(item.quantity) if item.quantity >= 1 else 1 for item in self.items.all())

    def __str__(self):
        if self.user:
            return f"Cart for User {self.user.username}"
        return f"Cart for Session {self.session_key}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('session_key',),
                condition=models.Q(user__isnull=True),
                name='unique_guest_cart_session',
            ),
        ]


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('store.Products', on_delete=models.CASCADE)
    quantity = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        default=Decimal('1.000'),
        validators=[MinValueValidator(Decimal('0.250'))]
    )
    cut_preference = models.CharField(max_length=100, default='Curry Cut (Medium)')
    delivery_slot = models.CharField(max_length=100, default='Express Delivery (45-60 Mins)')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'product')

    @property
    def subtotal(self):
        return (self.product.price * self.quantity).quantize(Decimal('0.01'))

    def __str__(self):
        return f"{self.quantity}kg x {self.product.name} in Cart #{self.cart.id}"
