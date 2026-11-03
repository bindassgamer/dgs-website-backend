"""Settings shared by every environment.

dev.py and prod.py import everything from here and add what differs. Pick one
with DJANGO_CONFIGURATION (see manage.py, wsgi.py and asgi.py).
"""
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


def env_list(name, default=""):
    return [
        item.strip()
        for item in os.environ.get(name, default).split(",")
        if item.strip()
    ]


BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")


def get_database(ssl_require=False):
    """PostgreSQL from expound_POSTGRES_URL, otherwise a local SQLite file."""
    postgres_url = clean_db_url(os.environ.get("expound_POSTGRES_URL"))
    database = dj_database_url.parse(
        postgres_url or f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=0,
        # SQLite has no SSL, so only require it for Postgres.
        ssl_require=bool(postgres_url) and ssl_require,
    )
    database["DISABLE_SERVER_SIDE_CURSORS"] = True
    return database


S3_ENDPOINT_URL = os.environ.get("S3_ENDPOINT_URL")
SUPABASE_PROJECT_REF = os.environ.get("SUPABASE_PROJECT_REF", "")


STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"
    },
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


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "backend.geo.apps.GeoConfig",
    "backend.people.apps.PeopleConfig",
    "backend.projects.apps.ProjectsConfig",
    "backend.channel_partners.apps.ChannelPartnersConfig",
    "backend.analytics.apps.AnalyticsConfig",
    "backend.careers.apps.CareersConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# The API is public and cookie-free, so any website (localhost included) may
# call it, as in the ET ERP backend. The admin is not part of /api/.
CORS_ALLOW_ALL_ORIGINS = True
CORS_URLS_REGEX = r"^/api/.*$"

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

# Throttle counters live here. A database cache is shared by every worker
# process (a per-process cache would multiply each limit by the worker
# count). The table is created by analytics migration 0002.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "django_cache",
        "OPTIONS": {"MAX_ENTRIES": 10000},
    }
}

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
