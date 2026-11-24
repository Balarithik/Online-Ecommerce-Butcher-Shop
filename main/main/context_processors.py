from django.conf import settings
from store.models import StorePricing

def site_settings(request):
    return {
        'settings': settings,
        'common_price_per_kg': StorePricing.get_common_price(),
    }
