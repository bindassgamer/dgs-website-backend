"""Production: set DJANGO_CONFIGURATION=production (wsgi.py and asgi.py
already default to it)."""
import os

from django.core.exceptions import ImproperlyConfigured

from config.settings.common import *  # noqa: F401,F403
from config.settings.common import env_list, get_database

DEBUG = False

SECRET_KEY = (
    os.environ.get("DJANGO_SECRET_KEY")
    or os.environ.get("expound")  # name used by earlier deployments
)
if not SECRET_KEY:
    raise ImproperlyConfigured("Set DJANGO_SECRET_KEY.")

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS")
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured(
        "Set DJANGO_ALLOWED_HOSTS to the host names this site is served on."
    )
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

DATABASES = {"default": get_database(ssl_require=True)}

# Number of reverse proxies in front of Django (0 when it is exposed
# directly). DRF uses it to read the real client IP from X-Forwarded-For,
# which stops clients from spoofing that header to dodge throttling.
NUM_PROXIES = int(os.environ.get("DJANGO_NUM_PROXIES", "1"))
REST_FRAMEWORK = {"NUM_PROXIES": NUM_PROXIES}
if NUM_PROXIES:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
