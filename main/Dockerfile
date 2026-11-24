# ==========================================
# Main Backend Dockerfile (Django + Gunicorn)
# ==========================================
FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.19 /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Refresh the lock for the security-patched exact pins in pyproject.toml, then install production dependencies.
# CI uses the same four-package refresh; this prevents Render from failing when uv.lock drifts.
COPY pyproject.toml uv.lock /app/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv lock --upgrade-package certifi --upgrade-package pillow --upgrade-package sqlparse --upgrade-package urllib3 \
    && uv sync --locked --no-dev --no-install-project

# Copy application source code
COPY . /app/

# COPY . /app/ overwrites the refreshed lockfile with the repository version.
# Refresh again after copying source so the final locked sync uses the current pins.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv lock --upgrade-package certifi --upgrade-package pillow --upgrade-package sqlparse --upgrade-package urllib3 \
    && uv sync --locked --no-dev --no-install-project

# Ensure entrypoint script is executable with Unix line endings
RUN chmod +x /app/entrypoint.sh && sed -i 's/\r$//' /app/entrypoint.sh

# Expose Django port
EXPOSE 8000

# Health check using Python (avoids installing curl)
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz/')" || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--threads", "2", "--timeout", "120", "main.wsgi:application"]
