from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET


@require_GET
@never_cache
def health_check(request):
    response = JsonResponse({"status": "ok"})
    response["Access-Control-Allow-Origin"] = "*"
    response["Cache-Control"] = "no-store"
    return response
