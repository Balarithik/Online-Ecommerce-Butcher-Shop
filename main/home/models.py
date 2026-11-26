from django.conf import settings
from django.db import models
from django.db.models import Q


class CustomerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="customer_profile",
    )
    mobile = models.CharField(max_length=10, blank=True)
    number_of_orders = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Profile for {self.user.username}"


class CustomerAddress(models.Model):
    LABEL_CHOICES = [
        ("Home", "Home"),
        ("Work", "Work"),
        ("Other", "Other"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_addresses",
    )
    label = models.CharField(max_length=10, choices=LABEL_CHOICES, default="Home")
    recipient_name = models.CharField(max_length=100)
    mobile = models.CharField(max_length=10)
    address = models.CharField(max_length=500)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    

    class Meta:
        ordering = ("-is_default", "created_at", "pk")
        constraints = [
            models.UniqueConstraint(
                fields=("user",),
                condition=Q(is_default=True),
                name="one_default_address_per_user",
            ),
        ]

    def __str__(self):
        return f"{self.label} address for {self.user.username}"

    @property
    def formatted_address(self):
        return self.address


class CustomerFeedback(models.Model):
    CATEGORY_CHOICES = [
        ("website", "Website experience"),
        ("products", "Products and pricing"),
        ("ordering", "Cart and checkout"),
        ("delivery", "Delivery experience"),
        ("other", "Other"),
    ]

    RATING_CHOICES = [(value, str(value)) for value in range(1, 6)]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="submitted_feedback",
    )
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="website")
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    message = models.TextField(max_length=1500)
    contact_email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Feedback ({self.get_category_display()}) - {self.rating}/5"
