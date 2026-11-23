import logging

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

logger = logging.getLogger(__name__)

# #region agent log
_AGENT_LOG_PATH = Path(__file__).resolve().parents[2] / "debug-3df742.log"


def _agent_log(hypothesis_id, location, message, data, run_id="post-fix"):
    try:
        payload = {
            "sessionId": "3df742",
            "runId": run_id,
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data,
            "timestamp": int(time.time() * 1000),
        }
        with _AGENT_LOG_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")
    except OSError:
        pass
# #endregion


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
