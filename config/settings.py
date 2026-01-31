"""
Django settings for config project.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""

from __future__ import annotations

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import environs

env = environs.Env()

BASE_DIR = environs.Path(__file__).resolve(strict=True).parent.parent

SECRET_KEY = env.str("SECRET_KEY", default="secret")

DEBUG = env.bool("DJANGO_DEBUG", default=False)

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["*"])
CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=[
        "https://grorg.defna.org",
        "http://localhost/",
    ],
)

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            str(BASE_DIR.joinpath("templates")),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
            "debug": DEBUG,
        },
    }
]

LOGIN_REDIRECT_URL = "/"

# Application definition

INSTALLED_APPS = (
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.messages",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.staticfiles",
    "django_prodserver",
    "django_tailwind_cli",
    "health_check",
    "health_check.db",
    "health_check.storage",
    "health_check.contrib.migrations",
    "django_q",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.github",
    "users",
    "grants",
)

MIDDLEWARE = (
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
)

ROOT_URLCONF = "config.urls"

WSGI_APPLICATION = "config.wsgi.application"

AUTH_USER_MODEL = "users.User"
LOGOUT_REDIRECT_URL = "/"

# Database
# https://docs.djangoproject.com/en/dev/ref/settings/#databases

DATABASES = {
    "default": env.dj_db_url("DATABASE_URL", default="sqlite:///db.sqlite3"),
}

# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/dev/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = "staticfiles"
STATICFILES_DIRS = (
    str(BASE_DIR.joinpath("frontend")),
    str(BASE_DIR.joinpath("static")),
)

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

# Django Allauth settings

ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"
ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_USERNAME_REQUIRED = False
LOGIN_REDIRECT_URL = "/"
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True

# django-prodserver settings

PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {"bind": "0.0.0.0:8000", "workers": "2"},
    },
    "worker": {
        "BACKEND": "django_prodserver.backends.django_q2.DjangoQ2Worker",
        "ARGS": {},
    },
}

# django-q settings

Q_CLUSTER = {
    "bulk": 10,
    "max_attempts": 1,
    "name": "DjangORM",
    "orm": "default",
    "queue_limit": 50,
    "retry": 120,
    "timeout": 90,
    "workers": 2,
}

# Tailwind CSS settings

TAILWIND_CLI_AUTOMATIC_DOWNLOAD = env.bool(
    "TAILWIND_CLI_AUTOMATIC_DOWNLOAD", default=True
)
TAILWIND_CLI_CONFIG_FILE = env.str(
    "TAILWIND_CLI_CONFIG_FILE", default="tailwind.config.js"
)
TAILWIND_CLI_DIST_CSS = env.str("TAILWIND_CLI_DIST_CSS", default="css/tailwind.css")
TAILWIND_CLI_PATH = str(environs.Path(env.str("TAILWIND_CLI_PATH", default="~/.local/bin/")).expanduser())
TAILWIND_CLI_SRC_CSS = env.str("TAILWIND_CLI_SRC_CSS", default="frontend/index.css")
TAILWIND_CLI_VERSION = env.str("TAILWIND_CLI_VERSION", default="4.1.18")
