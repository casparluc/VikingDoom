"""
Django settings for Vikingdoom project.

Generated by 'django-admin startproject' using Django 1.10.3.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""

import os
# Required for application using django outside the server
from django.conf.global_settings import *

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'your_secret_key_here'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'game.apps.GameConfig',
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

ROOT_URLCONF = 'Vikingdoom.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'Vikingdoom.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'db_engine',
        'NAME': 'db_name',
        'HOST': 'db_host',
        'PORT': 'db_port',
        'USER': 'db_user',
        'PASSWORD': 'db_password',
        'CHARSET': 'utf-8',
        'CON_MAX_AGE': 500,
        'OPTIONS': {
            'sql_mode': 'STRICT_ALL_TABLES'}
    }
}


# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/1.10/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/London'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Set the serializer used by the session manager
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = '/path/to/your/static/folder/'

# Configure logging for the game app
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': "%(asctime)s %(filename)s - %(levelname)s in %(module)s.%(funcName)s at line %(lineno)d:"
                      " %(message)s"
        },
        'compact': {
            'format': "%(asctime)s - %(levelname)s: %(message)s"
        }
    },
    'handlers': {
        'console': {
            'level': 'WARNING',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'game': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, "game/logs/game.log"),
            'formatter': 'simple'
        },
        'views': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, "game/logs/game_views.log"),
            'formatter': 'simple'
        },
        'dm_debug': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, "game/logs/actors_debug.log"),
            'formatter': 'compact'
        },
        'dm_info': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, "game/logs/actors_info.log"),
            'formatter': 'compact'
        },
        'dm_warn': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, "game/logs/actors_warn.log"),
            'formatter': 'compact'
        },
        'dm_error': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, "game/logs/actors_error.log"),
            'formatter': 'compact'
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'WARNING'
        },
        'Game': {
            'handlers': ['game', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'Game.Views': {
            'handlers': ['views', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'Game.dm.debug': {
            'handlers': ['dm_debug'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'Game.dm.info': {
            'handlers': ['dm_info'],
            'level': 'INFO',
            'propagate': False,
        },
        'Game.dm.warn': {
            'handlers': ['dm_warn', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'Game.dm.error': {
            'handlers': ['dm_error', 'console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

ADMINS = [('Your Name', 'your_email@address.com')]
