import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

# Configuration par variables d'environnement (voir .env.example). Sans rien définir, le projet
# démarre en mode développement (DEBUG activé, clé de développement non secrète).
DEBUG = os.environ.get("DJANGO_DEBUG", "True") == "True"

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured("Définissez DJANGO_SECRET_KEY quand DJANGO_DEBUG=False.")
    SECRET_KEY = "django-insecure-cle-de-developpement-uniquement"

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,[::1]").split(",")


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',

    'core',
    'accounts',
    'products',
    'cart',
    'orders',
    'payments',
    'dashboard',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ajaley.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'cart.context_processors.cart_context',
                'core.context_processors.site_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'ajaley.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'fr'
TIME_ZONE = 'Africa/Dakar'
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ('fr', 'Français'),
    ('en', 'English'),
]

LOCALE_PATHS = [BASE_DIR / 'locale']

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'accounts:profile'
LOGOUT_REDIRECT_URL = 'core:home'


# ---- Informations de la marque AJA LEY ----
SITE_NAME = "AJA LEY"
SITE_SLOGAN = "FOR EVERY MOOD. EVERY YOU."
WHATSAPP_SENEGAL = "+221776990926"
WHATSAPP_SENEGAL_DISPLAY = "+221 77 699 09 26"
WHATSAPP_INTL = "+13173199999"
WHATSAPP_INTL_DISPLAY = "+1 317 319 9999"
WHATSAPP_LINK = "https://wa.me/c/13173199999"
INSTAGRAM_HANDLE = "@ajaley.us"
INSTAGRAM_LINK = "https://www.instagram.com/ajaley.us"

# Frais de livraison au Sénégal (FCFA) — « zones de livraison AJA LEY » :
#   Dakar  : Dakar-ville SHIPPING_DAKAR / banlieue dakaroise SHIPPING_DAKAR_BANLIEUE
#   Thiès  : Thiès-ville SHIPPING_THIES / autre localité de la région SHIPPING_THIES_OTHER
#   Autres régions : SHIPPING_OTHER_REGIONS
# (Le modèle ShippingRate permet, si besoin, de surcharger le tarif d'une région SANS zones.)
# International : jamais de tarif automatique, les frais sont « à confirmer ».
SHIPPING_DAKAR = 2000
SHIPPING_DAKAR_BANLIEUE = 4000
SHIPPING_THIES = 1000
SHIPPING_THIES_OTHER = 2000
SHIPPING_OTHER_REGIONS = 2000
