import logging

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

logger = logging.getLogger(__name__)




@require_GET
@never_cache
def health_check(request):
    response = JsonResponse({"status": "ok"})
    response["Access-Control-Allow-Origin"] = "*"
    response["Cache-Control"] = "no-store"
    return response


def csrf_failure(request, reason=""):
    """Log CSRF failures without exposing token values, then show Django's page."""
    logger.warning(
        "CSRF failure on %s %s (%s); cookie=%s post_token=%s secure=%s",
        request.method,
        request.path,
        reason,
        "csrftoken" in request.COOKIES,
        bool(request.POST.get("csrfmiddlewaretoken")),
        request.is_secure(),
    )
    return render(
        request,
        "403_csrf.html",
        {"reason": reason},
        status=403,
    )


def page_not_found(request, exception):
    """Render the branded not-found page without exposing requested internals."""
    return render(request, "404.html", status=404)


def server_error(request):
    """Render a safe branded server-error page; details stay in server logs."""
    return render(request, "500.html", status=500)
