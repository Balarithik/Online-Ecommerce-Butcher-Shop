import json
import logging

import requests
from django.conf import settings


logger = logging.getLogger(__name__)


def _recipient_number(mobile):
    digits = ''.join(character for character in (mobile or '') if character.isdigit())
    country_code = settings.ORDER_NOTIFICATION_COUNTRY_CODE or '91'
    if len(digits) == 10:
        digits = f'{country_code}{digits}'
    return f'+{digits}' if digits else ''


def _sender_number(value, whatsapp=False):
    if not value:
        return ''
    if whatsapp:
        return value if value.startswith('whatsapp:') else f'whatsapp:{value}'
    return value


def _message_url():
    return (
        f'https://api.twilio.com/2010-04-01/Accounts/'
        f'{settings.TWILIO_ACCOUNT_SID}/Messages.json'
    )


def _send_message(channel, payload):
    try:
        response = requests.post(
            _message_url(),
            data=payload,
            auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN),
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException:
        logger.exception('Unable to send %s order confirmation.', channel)
        return False
    return True


def send_order_confirmation(order):
    """Send configured confirmation channels without affecting the saved order."""
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        return {'sms': False, 'whatsapp': False}

    recipient = _recipient_number(order.mobile)
    if not recipient:
        logger.warning('Order #%s has no valid mobile number for confirmation.', order.order_id)
        return {'sms': False, 'whatsapp': False}

    message = (
        f'Lakshmi Broliers: your order #{order.order_id} for '
        f'{order.product_name} has been confirmed. Total: Rs. {order.price}. '
        f'Delivery: {order.delivery_slot}.'
    )
    results = {'sms': False, 'whatsapp': False}

    sms_sender = _sender_number(settings.TWILIO_SMS_FROM)
    if sms_sender:
        results['sms'] = _send_message('SMS', {
            'From': sms_sender,
            'To': recipient,
            'Body': message,
        })

    whatsapp_sender = _sender_number(settings.TWILIO_WHATSAPP_FROM, whatsapp=True)
    if whatsapp_sender:
        whatsapp_payload = {
            'From': whatsapp_sender,
            'To': f'whatsapp:{recipient}',
        }
        if settings.TWILIO_WHATSAPP_CONTENT_SID:
            whatsapp_payload['ContentSid'] = settings.TWILIO_WHATSAPP_CONTENT_SID
            whatsapp_payload['ContentVariables'] = json.dumps({
                '1': str(order.order_id),
                '2': order.product_name,
                '3': str(order.price),
                '4': order.delivery_slot,
            })
        else:
            whatsapp_payload['Body'] = message
        results['whatsapp'] = _send_message('WhatsApp', whatsapp_payload)

    return results
