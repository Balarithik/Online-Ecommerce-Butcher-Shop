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


class StoreSettings(models.Model):
    """Singleton-like store-wide pricing configuration managed from inventory."""
    common_price_per_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="When saved, this rate is applied to every product currently in the catalog.",
    )
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def current(cls):
        return cls.objects.first()

    def __str__(self):
        return f"Common price: ₹{self.common_price_per_kg}/kg"
