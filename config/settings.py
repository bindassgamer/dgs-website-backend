import os
from pathlib import Path
import dj_database_url
from urllib.parse import urlsplit, urlunsplit

from dotenv import load_dotenv


def clean_db_url(url):
    if not url:
        return url
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

MEDIA_URL = "/files/"
MEDIA_ROOT = Path(os.environ.get("DJANGO_MEDIA_ROOT", BASE_DIR / "files"))

S3_ENDPOINT_URL = os.environ.get("S3_ENDPOINT_URL")
SUPABASE_PROJECT_REF = os.environ.get("SUPABASE_PROJECT_REF", "")


STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}


if S3_ENDPOINT_URL:
    STORAGES["default"] = {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "bucket_name": "media",
            "endpoint_url": S3_ENDPOINT_URL,
            "access_key": os.environ.get("S3_ACCESS_KEY"),
            "secret_key": os.environ.get("S3_SECRET_KEY"),
            "region_name": os.environ.get("S3_REGION", "ap-south-1"),
            "custom_domain": (
                f"{SUPABASE_PROJECT_REF}.supabase.co"
                "/storage/v1/object/public/media"
            ),
            "querystring_auth": False,
            "file_overwrite": False,
            "addressing_style": "path",
        },
    }


SECRET_KEY = os.environ.get(
    "expound",
    "django-insecure-local-development-key-change-before-deploying",
)
DEBUG = os.environ.get("DJANGO_DEBUG", "true").lower() == "true"
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get(
        "DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1"
    ).split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "backend.people.apps.PeopleConfig",
    "backend.projects.apps.ProjectsConfig",
    "backend.channel_partners.apps.ChannelPartnersConfig",
    "backend.analytics.apps.AnalyticsConfig",
    "backend.careers.apps.CareersConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": dj_database_url.parse(
        clean_db_url(os.environ.get("expound_POSTGRES_URL"))
        or f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=0,
        ssl_require=not DEBUG,
    )
}
DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation.MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation.CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/files/"
MEDIA_ROOT = Path(os.environ.get("DJANGO_MEDIA_ROOT", BASE_DIR / "files"))

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
