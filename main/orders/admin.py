from django.contrib import admin
from . import models
# Register your models here.

admin.site.register(models.Order)



@admin.register(models.NotificationDelivery)
class NotificationDeliveryAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "channel", "event", "recipient", "status", "attempt_count", "sent_at")
    list_filter = ("channel", "event", "status")
    search_fields = ("recipient", "order__order_id", "provider_message_id")
    readonly_fields = ("order", "channel", "event", "recipient", "status", "attempt_count",
                       "provider_message_id", "last_error", "next_attempt_at", "sent_at",
                       "created_at", "updated_at")
    ordering = ("-created_at",)
