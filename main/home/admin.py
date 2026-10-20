from django.contrib import admin
from .models import CustomerProfile, CustomerAddress

@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'mobile')
    search_fields = ('user__username', 'mobile')

@admin.register(CustomerAddress)
class CustomerAddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'label', 'recipient_name', 'mobile', 'is_default')
    list_filter = ('label', 'is_default')
    search_fields = ('user__username', 'recipient_name', 'mobile', 'address')


