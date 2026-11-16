"""Django settings for the Infillo API. Values that differ between machines come from .env."""

from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

INSTALLED_APPS = [
    # Django's built-in apps (admin, auth, sessions...) — each brings its own models and migrations
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "corsheaders",
    # Our apps
    "apps.core",
    "apps.accounts",
]

# Must be set before the first migrate
AUTH_USER_MODEL = "accounts.User"
# Log in with e-mail or username (also in the Django admin). Replaces the default ModelBackend;
# ours extends it, so permission checks keep working.
AUTHENTICATION_BACKENDS = ["apps.accounts.backends.EmailOrUsernameBackend"]


# Password rules used by validate_password() in RegisterSerializer (Django has none by default).
# Minimum length is 8 (the default of MinimumLengthValidator).
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

MIDDLEWARE = [
    # CORS must run before anything that can return a response
    "corsheaders.middleware.CorsMiddleware",
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
        # Needed only by the Django admin (our UI is the Next.js frontend)
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {"default": env.db("DATABASE_URL")}
# Fail fast instead of hanging when the database is down (/health reports the error)
DATABASES["default"]["OPTIONS"] = {"connect_timeout": 5}

LANGUAGE_CODE = "pl"
TIME_ZONE = "Europe/Warsaw"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# API paths have no trailing slash (/health, /auth/login) — same contract as before
APPEND_SLASH = False

CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=["http://localhost:3000"])
CORS_ALLOW_CREDENTIALS = True

REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": "apps.core.exceptions.api_exception_handler",
    # Token from the httpOnly cookie, user loaded from the database
    "DEFAULT_AUTHENTICATION_CLASSES": ["apps.accounts.authentication.CookieJWTAuthentication"],
    # Closed by default; public views opt out with AllowAny
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    # JSON only: together with SameSite=Lax this is our CSRF protection (R1)
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.StandardPagination",
}

# JWT in a cookie: 8 h, no refresh token
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=8),
    "SIGNING_KEY": env("JWT_SECRET"),  # separate from SECRET_KEY
}
AUTH_COOKIE_NAME = "infillo_access_token"
AUTH_COOKIE_SECURE = env.bool("AUTH_COOKIE_SECURE", default=False)  # True behind HTTPS
AUTH_COOKIE_SAMESITE = "Lax"
