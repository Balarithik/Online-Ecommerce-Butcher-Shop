from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

# Create your models here.
class Products(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    # Money must not be stored as a float: floating point rounding can change totals.
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    is_available = models.BooleanField(default=True)
    description = models.TextField()
    image1 = models.ImageField(upload_to='products_images/')
    image2 = models.ImageField(upload_to='products_images/', blank=True, null=True)
    image3 = models.ImageField(upload_to='products_images/', blank=True, null=True)
    image4 = models.ImageField(upload_to='products_images/', blank=True, null=True)

    def __str__(self):
        return self.name
