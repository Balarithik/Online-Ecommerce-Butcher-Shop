from django.db import models

# Create your models here.
class Products(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    price = models.FloatField()
    description = models.TextField()
    image1 = models.ImageField(upload_to='products_images/')
    image2 = models.ImageField(upload_to='products_images/', blank=True, null=True)
    image3 = models.ImageField(upload_to='products_images/', blank=True, null=True)
    image4 = models.ImageField(upload_to='products_images/', blank=True, null=True)

    def __str__(self):
        return self.name