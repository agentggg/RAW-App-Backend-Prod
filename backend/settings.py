from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
import os
import environ
env = environ.Env()
environ.Env.read_env()# reading .env file



# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRETKEY")
# https://www.random.org/passwords/?mode=advanced

DEBUG = True

ALLOWED_HOSTS = ['*']

BASE_URL = "http://localhost:8000"


INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'app_backend',
    'django_extensions',
    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    'django_celery_beat',
    'django.contrib.admin',
    'django_bootstrap5',
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware'
]

EMAIL_BACKEND = env("EMAIL_BACKEND")
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_PORT = env("EMAIL_PORT")
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
SERVER_EMAIL = env("SERVER_EMAIL")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False

ADMINS = [
    ("Stevenson Gerard Eustache", "tech.and.faith.contact@gmail.com")
]
# send emails and debug error to admins

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'app_backend/templates')],
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

WSGI_APPLICATION = 'backend.wsgi.application'
# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases


#https://stackoverflow.com/questions/43612243/install-mysqlclient-for-django-python-on-mac-os-x-sierra/54521244
#https://python.plainenglish.io/connect-django-with-database-43f1965565e0
DATABASES = {
    # 'default': {
    #     'ENGINE': env("ENGINE_NAME"),
    #     'NAME': env("DATABASE_NAME"), #Database Name
    #     'USER': env("DATABASE_USER"), #Your Postgresql user
    #     'PASSWORD': env("DATABASE_PASSWORD"), #Your Postgresql password
    #     'HOST': env("DATABASE_HOST"),
    #     'PORT': env("DATABASE_PORT")
    # },
    # 'OPTIONS': {
    #     'init_command': "SET sql_mode='STRICT_TRANS_TABLES'"
    #     }    
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


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
# https://docs.djangoproject.com/en/3.2/topics/i18n/


LANGUAGE_CODE = 'en-us'
TIME_ZONE='UTC'
DATETIME_FORMAT="%Y-%m-%d%H:%M:%S"
L10N=False
USE_TZ=False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.normpath(os.path.dirname(__file__))
STATIC_URL = '/staticfiles/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'staticfiles'), ]

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CACHES = {
    "default": {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        "LOCATION": "test_table",
        "OPTIONS": {
            "timeout": 1,
            "MAX_ENTRIES" : 4
        }
    }
}

# django_heroku.settings(locals())

AUTH_USER_MODEL = "app_backend.CustomUser"  # new
# # custom user model database for login


BROKER_URL = 'redis://default:E2xKDfM6KmrMfuViGh1bIJJPR5IaeuYs@redis-18012.c81.us-east-1-2.ec2.cloud.redislabs.com:18012'
INTERNAL_IPS = [
    "127.0.0.1",
    "192.168.0.194",
    # for Django debug interface
]
