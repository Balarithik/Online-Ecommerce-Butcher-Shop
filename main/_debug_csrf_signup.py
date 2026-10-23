"""Temporary CSRF signup reproduction script for debug session 3df742."""
import json
import os
import re
import time
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "main.settings")

import django

django.setup()

from django.core.management import call_command
from django.test import Client, override_settings

LOG_PATH = Path(__file__).resolve().parents[1] / "debug-3df742.log"


def agent_log(hypothesis_id, location, message, data):
    payload = {
        "sessionId": "3df742",
        "runId": "post-fix",
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data,
        "timestamp": int(time.time() * 1000),
    }
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


@override_settings(
    ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"],
    DEBUG=False,
    SESSION_COOKIE_SECURE=True,
    CSRF_COOKIE_SECURE=True,
    SECURE_SSL_REDIRECT=False,
    SECURE_PROXY_SSL_HEADER=("HTTP_X_FORWARDED_PROTO", "https"),
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    },
)
def main():
    call_command("migrate", verbosity=0, run_syncdb=True)
    token_re = re.compile(r'name="csrfmiddlewaretoken" value="([^"]+)"')

    csrf_client = Client(enforce_csrf_checks=True)
    page = csrf_client.get("/signup/")
    match = token_re.search(page.content.decode())
    cookie_present = "csrftoken" in csrf_client.cookies
    agent_log(
        "A",
        "_debug_csrf_signup.py:get",
        "signup GET csrf state",
        {
            "status": page.status_code,
            "has_form_token": bool(match),
            "has_cookie": cookie_present,
            "cache_control": page.get("Cache-Control"),
            "cookie_secure": csrf_client.cookies["csrftoken"].get("secure") if cookie_present else None,
            "cookie_samesite": csrf_client.cookies["csrftoken"].get("samesite") if cookie_present else None,
        },
    )

    bad = csrf_client.post(
        "/signup/",
        {
            "csrfmiddlewaretoken": "deadbeef",
            "username": "u1",
            "password1": "A-strong-password123",
            "password2": "A-strong-password123",
        },
    )
    agent_log(
        "D",
        "_debug_csrf_signup.py:bad_token",
        "post with wrong token",
        {"status": bad.status_code},
    )

    csrf_client2 = Client(enforce_csrf_checks=True)
    page2 = csrf_client2.get("/signup/")
    token2 = token_re.search(page2.content.decode()).group(1)
    ok = csrf_client2.post(
        "/signup/",
        {
            "csrfmiddlewaretoken": token2,
            "username": "csrfuser1",
            "password1": "A-strong-password123",
            "password2": "A-strong-password123",
        },
    )
    agent_log(
        "A",
        "_debug_csrf_signup.py:good_token",
        "post with matching token",
        {"status": ok.status_code, "location": ok.get("Location")},
    )

    csrf_client3 = Client(enforce_csrf_checks=True)
    page_a = csrf_client3.get("/signup/")
    token_a = token_re.search(page_a.content.decode()).group(1)
    cookie_a = csrf_client3.cookies["csrftoken"].value
    page_b = csrf_client3.get("/signup/")
    token_b = token_re.search(page_b.content.decode()).group(1)
    cookie_b = csrf_client3.cookies["csrftoken"].value
    stale = csrf_client3.post(
        "/signup/",
        {
            "csrfmiddlewaretoken": token_a,
            "username": "csrfuser2",
            "password1": "A-strong-password123",
            "password2": "A-strong-password123",
        },
    )
    agent_log(
        "B",
        "_debug_csrf_signup.py:stale_token",
        "post old form token after second GET",
        {
            "token_changed": token_a != token_b,
            "cookie_changed": cookie_a != cookie_b,
            "stale_status": stale.status_code,
            "cache_control_first": page_a.get("Cache-Control"),
            "cache_control_second": page_b.get("Cache-Control"),
        },
    )

    # Simulate production: HTTPS behind proxy + missing cache headers on signup
    prod_client = Client(enforce_csrf_checks=True)
    prod_page = prod_client.get(
        "/signup/",
        HTTP_X_FORWARDED_PROTO="https",
        secure=True,
    )
    prod_token = token_re.search(prod_page.content.decode())
    agent_log(
        "C",
        "_debug_csrf_signup.py:prod_like_get",
        "production-like HTTPS signup GET",
        {
            "status": prod_page.status_code,
            "has_form_token": bool(prod_token),
            "has_cookie": "csrftoken" in prod_client.cookies,
            "cache_control": prod_page.get("Cache-Control"),
            "cookie_secure": prod_client.cookies["csrftoken"].get("secure")
            if "csrftoken" in prod_client.cookies
            else None,
        },
    )
    if prod_token:
        prod_ok = prod_client.post(
            "/signup/",
            {
                "csrfmiddlewaretoken": prod_token.group(1),
                "username": "csrfuser3",
                "password1": "A-strong-password123",
                "password2": "A-strong-password123",
            },
            HTTP_X_FORWARDED_PROTO="https",
            secure=True,
            HTTP_ORIGIN="https://lakshmi-broliers.onrender.com",
            HTTP_REFERER="https://lakshmi-broliers.onrender.com/signup/",
        )
        agent_log(
            "C",
            "_debug_csrf_signup.py:prod_like_post",
            "production-like HTTPS signup POST",
            {"status": prod_ok.status_code, "location": prod_ok.get("Location")},
        )

    print("Wrote logs to", LOG_PATH)


if __name__ == "__main__":
    main()
