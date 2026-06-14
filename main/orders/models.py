from django.db import models

# Create your models here.

class Order(models.Model):
    status_choices = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    order_id = models.IntegerField(primary_key=True)
    product_id = models.IntegerField(null=True, blank=True)
    name = models.CharField(max_length=100)
    mobile = models.CharField(max_length=13,null=True, blank=True)
    quantity = models.FloatField(default=1  )
    price = models.FloatField()
    location = models.CharField(max_length=500,null=True, blank=True)
    instructions = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=status_choices, default='pending')
    
    def __str__(self):
        return f"Order {self.order_id} - {self.name} x {self.quantity}"
