import os

from django.core.wsgi import get_wsgi_application


# Servers (gunicorn) load this file, so unlike manage.py it defaults to
# production: forgetting DJANGO_CONFIGURATION must not start a debug server.
environment = os.environ.get("DJANGO_CONFIGURATION", "production")
if environment == "development":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
else:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")

application = get_wsgi_application()
