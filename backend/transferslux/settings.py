import io
import os
import sys
from pathlib import Path

from django.utils.translation import gettext_lazy as _
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv("SECRET_KEY", "1insecure1-1default1")

# DEBUG выключает кэш
DEBUG = False

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost 127.0.0.1 217.154.121.7").split()

CSRF_TRUSTED_ORIGINS = [
    "https://*.transferslux.com",
    "https://transferslux.com",
    "http://localhost",
    "http://127.0.0.1",
    "http://127.0.0.1:8000",
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',  # Для переводов чисел, дат и т.д.
    'django.contrib.sitemaps',
    'api.apps.ApiConfig',
    'meta',  # Meta теги для SEO
]

# Dev-only apps
if DEBUG:
    INSTALLED_APPS += ["django_browser_reload", "debug_toolbar"]

MIDDLEWARE = [
    # 1. GZip-сжатие (опционально, WhiteNoise уже сжимает статику)
    "django.middleware.gzip.GZipMiddleware",
    # 2. Безопасность
    "django.middleware.security.SecurityMiddleware",
    # 🔹 WhiteNoise — должен быть ЗДЕСЬ
    "whitenoise.middleware.WhiteNoiseMiddleware",
    # 3. Сессии (нужны до LocaleMiddleware)
    "django.contrib.sessions.middleware.SessionMiddleware",
    # 4. Локализация
    "django.middleware.locale.LocaleMiddleware",
    # 5. Общие заголовки и корректировка URL
    "django.middleware.common.CommonMiddleware",
    # 6. CSRF и аутентификация
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    # 7. Защита от iframe
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

if DEBUG:
    MIDDLEWARE += [
        "django_browser_reload.middleware.BrowserReloadMiddleware",
        "debug_toolbar.middleware.DebugToolbarMiddleware",
    ]

ROOT_URLCONF = 'transferslux.urls'

# Путь к директории с шаблонами вынесен в переменную:
TEMPLATES_DIR = BASE_DIR / 'templates'

# Путь к переводам:
LOCALE_PATHS = [BASE_DIR / 'locale']

# Google API
GOOGLE_MAPS_API_KEY = str(os.getenv("GOOGLE_API_KEY"))

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATES_DIR],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'api.context_processors.google_maps_api_key'
            ],
        },
    },
]

WSGI_APPLICATION = 'transferslux.wsgi.application'

# PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', 'transferslux'),
        'USER': os.getenv('POSTGRES_USER', 'transferslux_user'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', ''),
        'PORT': os.getenv('DB_PORT', 5432),
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

DEFAULT_CHARSET = "utf-8"
FILE_CHARSET = "utf-8"

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'

# Локализация языков
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ('en', _('English')),
    ('it', _('Italian')),
    ('es', _('Spanish')),
    ('fr', _('French')),
    ('ru', _('Russian')),
]

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'collected_static'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

if DEBUG:
    STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.dummy.DummyCache",
        }
    }
else:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": os.getenv("REDIS_URL", "redis://redis:6379/1"),
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                # "PASSWORD": os.getenv("REDIS_PASSWORD"),  # если настроена авторизация
            },
        }
    }

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.yandex.ru'
EMAIL_PORT = 465
EMAIL_USE_TLS = False
EMAIL_USE_SSL = True
EMAIL_HOST_USER = str(os.getenv("EMAIL_HOST_USER_DJANGO"))
EMAIL_HOST_PASSWORD = str(os.getenv("EMAIL_HOST_PASSWORD_DJANGO"))
DEFAULT_FROM_EMAIL = str(os.getenv("EMAIL_HOST_USER_DJANGO"))

# Post Office для управления email
EMAIL_BACKEND = 'post_office.EmailBackend'
POST_OFFICE = {
    'BACKENDS': {
        'default': 'django.core.mail.backends.smtp.EmailBackend',
    },
    'DEFAULT_PRIORITY': 'now',
    'CELERY_ENABLED': False,
}

# Контакты
CONTACT_PHONE = "+1-234-567-8900"
WHATSAPP_NUMBER = "12345678900"
CONTACT_EMAIL = "info@transferslux.com"

# SEO / верификация
GOOGLE_ANALYTICS_ID = os.getenv("GOOGLE_ANALYTICS_ID", "")
YANDEX_METRICA_ID = os.getenv("YANDEX_METRICA_ID", "")
BING_WEBMASTER_ID = os.getenv("BING_WEBMASTER_ID", "")
BING_UET_TAG = os.getenv("BING_UET_TAG", "")
GOOGLE_SITE_VERIFICATION = os.getenv("GOOGLE_SITE_VERIFICATION", "")
YANDEX_VERIFICATION = os.getenv("YANDEX_VERIFICATION", "")
BING_SITE_VERIFICATION = os.getenv("BING_SITE_VERIFICATION", "")

# Transfer API ключи
TRANSFER_API_KEY_1 = os.getenv("TRANSFER_API_KEY_1", "")
TRANSFER_API_KEY_2 = os.getenv("TRANSFER_API_KEY_2", "")
TRANSFERS_CACHE_TIMEOUT = int(os.getenv("TRANSFERS_CACHE_TIMEOUT", 3600))

# Настройки для пагинации
PAGINATE_BY = 20

# Настройки безопасности для загрузки файлов
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# Логирование
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "transfers_file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "/tmp/transfers.log",
            "formatter": "verbose",
        },
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "services.transfer_service": {
            "handlers": ["transfers_file", "console"],
            "level": "INFO",
            "propagate": True,
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "ERROR",
    },
}

# stdout fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
