"""Local development: run with `python manage.py runserver`."""
import os

from config.settings.common import *  # noqa: F401,F403
from config.settings.common import get_database

DEBUG = True
ALLOWED_HOSTS = ["*"]

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-local-development-key-change-before-deploying",
)

DATABASES = {"default": get_database()}

# No proxy in front of runserver, so the client address is the real one.
REST_FRAMEWORK = {"NUM_PROXIES": 0}
