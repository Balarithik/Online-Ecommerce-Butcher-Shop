"""Durable, database-backed customer notifications for Lakshmi Broilers."""
import logging
from datetime import timedelta
from urllib.parse import urljoin

import requests
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

from .models import NotificationDelivery

logger = logging.getLogger(__name__)
MAX_ATTEMPTS = 6
BACKOFF_MINUTES = (1, 5, 15, 60, 180, 360)


def enqueue_order_event(order, event):
    """Create one delivery per eligible channel; DB uniqueness makes this idempotent."""
    channels = ["email"]
    if order.whatsapp_opt_in:
        channels.append("whatsapp")
    if order.sms_opt_in:
        channels.append("sms")
    created = []
    for channel in channels:
        recipient = (order.user.email if order.user_id else "") if channel == "email" else (order.mobile or "")
        if not recipient:
            continue
        delivery, was_created = NotificationDelivery.objects.get_or_create(
            order=order, event=event, channel=channel,
            defaults={"recipient": recipient, "status": "pending"},
        )
        if was_created:
            created.append(delivery.pk)
    return created


def _order_context(delivery):
    order = delivery.order
    site_url = settings.NOTIFICATION_SITE_URL.rstrip("/") + "/"
    tracking_url = urljoin(site_url, f"orders/confirmation/{order.order_id}/")
    item_lines = [
        f"{item.product_name} — {item.quantity} kg"
        for item in order.items.all()
    ]
    if not item_lines and order.product_name:
        item_lines = [f"{order.product_name} — {order.quantity} kg"]
    return {"order": order, "event": delivery.event, "tracking_url": tracking_url,
            "item_lines": item_lines, "status_label": order.get_status_display()}


def _send_email(delivery):
    if not settings.RESEND_API_KEY:
        raise RuntimeError("RESEND_API_KEY is not configured")
    context = _order_context(delivery)
    response = requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {settings.RESEND_API_KEY}",
                 "Idempotency-Key": f"lb-order-{delivery.order_id}-{delivery.event}-email"},
        json={
            "from": settings.RESEND_FROM_EMAIL, "to": [delivery.recipient],
            "subject": f"Lakshmi Broilers: Order #{delivery.order_id} update",
            "text": render_to_string("notifications/order_update.txt", context),
            "html": render_to_string("notifications/order_update.html", context),
            "tags": [{"name": "order_id", "value": str(delivery.order_id)},
                     {"name": "event", "value": delivery.event}],
        }, timeout=15,
    )
    response.raise_for_status()
    delivery.provider_message_id = response.json().get("id", "")


def _send_whatsapp(delivery):
    required = (settings.WHATSAPP_CLOUD_ACCESS_TOKEN, settings.WHATSAPP_PHONE_NUMBER_ID,
                settings.WHATSAPP_ORDER_TEMPLATE)
    if not all(required):
        raise RuntimeError("WhatsApp Cloud API credentials/template are not fully configured")
    context = _order_context(delivery)
    digits = "".join(ch for ch in delivery.recipient if ch.isdigit())
    if len(digits) == 10:
        digits = settings.ORDER_NOTIFICATION_COUNTRY_CODE + digits
    if not 10 <= len(digits) <= 15:
        raise RuntimeError("Customer mobile number is invalid for WhatsApp")
    url = (f"https://graph.facebook.com/{settings.WHATSAPP_GRAPH_API_VERSION}/"
           f"{settings.WHATSAPP_PHONE_NUMBER_ID}/messages")
    response = requests.post(
        url, headers={"Authorization": f"Bearer {settings.WHATSAPP_CLOUD_ACCESS_TOKEN}"},
        json={
            "messaging_product": "whatsapp", "recipient_type": "individual",
            "to": digits, "type": "template",
            "template": {"name": settings.WHATSAPP_ORDER_TEMPLATE,
                "language": {"code": settings.WHATSAPP_TEMPLATE_LANGUAGE},
                "components": [{"type": "body", "parameters": [
                    {"type": "text", "text": str(delivery.order_id)},
                    {"type": "text", "text": context["status_label"]},
                    {"type": "text", "text": str(delivery.order.price)},
                    {"type": "text", "text": context["tracking_url"]},
                ]}]},
        }, timeout=15,
    )
    response.raise_for_status()
    messages = response.json().get("messages") or []
    delivery.provider_message_id = messages[0].get("id", "") if messages else ""


def _send_sms(delivery):
    """Send a DLT-approved transactional SMS through MSG91 Flow API."""
    if not settings.MSG91_AUTH_KEY or not settings.MSG91_SMS_TEMPLATE_ID:
        raise RuntimeError("MSG91_AUTH_KEY and MSG91_SMS_TEMPLATE_ID must be configured")

    digits = "".join(ch for ch in delivery.recipient if ch.isdigit())
    if len(digits) == 10:
        digits = settings.ORDER_NOTIFICATION_COUNTRY_CODE + digits
    if not 10 <= len(digits) <= 15:
        raise RuntimeError("Customer mobile number is invalid for SMS")

    context = _order_context(delivery)
    response = requests.post(
        "https://control.msg91.com/api/v5/flow",
        headers={
            "accept": "application/json",
            "authkey": settings.MSG91_AUTH_KEY,
            "content-type": "application/json",
        },
        json={
            "template_id": settings.MSG91_SMS_TEMPLATE_ID,
            "short_url": "0",
            "recipients": [{
                "mobiles": digits,
                "VAR1": str(delivery.order_id),
                "VAR2": context["status_label"],
                "VAR3": str(delivery.order.price),
            }],
        },
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("type") != "success" or payload.get("hasError") is True:
        reason = payload.get("message") or payload.get("errors") or "MSG91 rejected the SMS request"
        raise RuntimeError(f"MSG91 SMS error: {reason}")
    delivery.provider_message_id = str(payload.get("message", ""))


def deliver_notification(delivery):
    """Attempt delivery and persist bounded retry state."""
    try:
        if delivery.channel == "email":
            _send_email(delivery)
        elif delivery.channel == "whatsapp":
            _send_whatsapp(delivery)
        elif delivery.channel == "sms":
            _send_sms(delivery)
        else:
            raise RuntimeError("Unsupported notification channel")
    except (requests.RequestException, RuntimeError, ValueError) as exc:
        delivery.attempt_count += 1
        delivery.last_error = str(exc)[:1000]
        if delivery.attempt_count >= MAX_ATTEMPTS:
            delivery.status = "failed"
            delivery.next_attempt_at = None
        else:
            delivery.status = "pending"
            delay = BACKOFF_MINUTES[min(delivery.attempt_count - 1, len(BACKOFF_MINUTES) - 1)]
            delivery.next_attempt_at = timezone.now() + timedelta(minutes=delay)
        delivery.save(update_fields=["attempt_count", "last_error", "status",
                                     "next_attempt_at", "updated_at"])
        logger.warning("Notification %s failed: %s", delivery.pk, delivery.last_error)
        return False
    delivery.status = "sent"
    delivery.attempt_count += 1
    delivery.sent_at = timezone.now()
    delivery.last_error = ""
    delivery.next_attempt_at = None
    delivery.save(update_fields=["status", "attempt_count", "sent_at", "last_error",
                                 "next_attempt_at", "provider_message_id", "updated_at"])
    return True
