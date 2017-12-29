"""
Django settings for votingsite project.

Generated by 'django-admin startproject' using Django 2.0.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Application definition
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'polls',
    'accounts',
]

AUTH_USER_MODEL = 'accounts.User'
AUTHENTICATION_BACKENDS = [
    'accounts.authentication.PasswordlessAuthenticationBackend',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'votingsite.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['polls/templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'votingsite.wsgi.application'

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/Los_Angeles'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'

DEFAULT_FROM_EMAIL = 'Admin <noreply@miniscruff.com>'
MANAGERS = (
    ('Ronnie', 'halfpint1170@gmail.com')
)

# Load secrets and environment specific settings based on which
# environment we are currently in
if 'CI' in os.environ:
    SECRET_KEY = os.environ['SECRET_KEY']
    DEBUG = True
    ALLOWED_HOSTS = []

    EMAIL_USE_TLS = True
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_HOST_USER = os.environ['GMAIL_USER']
    EMAIL_HOST_PASSWORD = os.environ['GMAIL_PASSWORD']
    EMAIL_PORT = 587

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }

elif 'HEROKU' in os.environ:
    SECRET_KEY = os.environ['SECRET_KEY']
    DEBUG = False
    ALLOWED_HOSTS = ['minivote.herokuapp.com', 'minivotestaging.herokuapp.com']

    EMAIL_USE_TLS = True
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_HOST_USER = os.environ['GMAIL_USER']
    EMAIL_HOST_PASSWORD = os.environ['GMAIL_PASSWORD']
    EMAIL_PORT = 587

    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

    import dj_database_url
    DATABASES = {
        'default': dj_database_url.config()
    }

    STATICFILES_STORAGE = 'whitenoise.django.GzipManifestStaticFilesStorage'
    MIDDLEWARE.append('whitenoise.middleware.WhiteNoiseMiddleware')

else:
    # local settings
    from votingsite import local_config
    SECRET_KEY = local_config.APP_SECRET_KEY
    DEBUG = local_config.APP_DEBUG
    ALLOWED_HOSTS = local_config.APP_ALLOWED_HOSTS

    EMAIL_USE_TLS = local_config.EMAIL_USE_TLS
    EMAIL_HOST = local_config.EMAIL_HOST
    EMAIL_HOST_USER = local_config.EMAIL_HOST_USER
    EMAIL_HOST_PASSWORD = local_config.EMAIL_HOST_PASSWORD
    EMAIL_PORT = local_config.EMAIL_PORT

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, '../database/db.sqlite3'),
        }
    }
