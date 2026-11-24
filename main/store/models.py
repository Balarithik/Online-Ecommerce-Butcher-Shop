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

    @property
    def display_price(self):
        return get_common_price()

    def __str__(self):
        return self.name


class StorePricing(models.Model):
    """Single shop-wide per-kilogram price managed from the admin inventory page."""
    common_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('240.00'),
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Store pricing"
        verbose_name_plural = "Store pricing"

    def __str__(self):
        return f"Common price: ₹{self.common_price}/kg"

    @classmethod
    def get_common_price(cls):
        setting = cls.objects.order_by('pk').first()
        return setting.common_price if setting else Decimal('240.00')


def get_common_price():
    return StorePricing.get_common_price()


def get_product_price(product):
    return get_common_price()
