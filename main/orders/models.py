from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

# Create your models here.

class Order(models.Model):
    status_choices = [
        ('pending', 'Pending'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled')
    ]

    order_id = models.AutoField(primary_key=True)
    product_id = models.IntegerField(null=True, blank=True)
    product_name = models.CharField(max_length=100,null=True)
    name = models.CharField(max_length=100)
    mobile = models.CharField(max_length=13,null=True, blank=True)
    quantity = models.DecimalField(max_digits=6, decimal_places=3, default=Decimal('1.000'), validators=[MinValueValidator(Decimal('0.250')), MaxValueValidator(Decimal('100.000'))])
    # This is the order-line total at purchase time, not the product's live price.
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    location = models.CharField(max_length=500,null=True, blank=True)
    instructions = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=status_choices, default='pending')
    
    def __str__(self):
        return f"Order {self.order_id} - {self.name} x {self.quantity}"
