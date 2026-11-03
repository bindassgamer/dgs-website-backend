import os

from django.core.asgi import get_asgi_application


# Like wsgi.py, this defaults to production.
environment = os.environ.get("DJANGO_CONFIGURATION", "production")
if environment == "development":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
else:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")

application = get_asgi_application()
