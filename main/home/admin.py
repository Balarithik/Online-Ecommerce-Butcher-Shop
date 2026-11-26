from django.contrib import admin
from .models import CustomerProfile, CustomerAddress, CustomerFeedback

@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'mobile')
    search_fields = ('user__username', 'mobile')

@admin.register(CustomerAddress)
class CustomerAddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'label', 'recipient_name', 'mobile', 'is_default')
    list_filter = ('label', 'is_default')
    search_fields = ('user__username', 'recipient_name', 'mobile', 'address')




@admin.register(CustomerFeedback)
class CustomerFeedbackAdmin(admin.ModelAdmin):
    list_display = ("created_at", "category", "rating", "user", "contact_email")
    list_filter = ("category", "rating", "created_at")
    search_fields = ("message", "contact_email", "user__username")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)
