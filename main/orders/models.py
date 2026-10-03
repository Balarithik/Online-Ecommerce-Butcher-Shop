from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from decimal import Decimal

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
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"Order #{self.order_id} - {self.name} ({self.product_name or 'Items'})"
