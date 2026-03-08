import os
from pathlib import Path
from django.contrib.messages import constants as messages

# 1. PATHS & SECURITY
BASE_DIR = Path(__file__).resolve().parent.parent

# TANDAAN: Sa production, ilipat ang SECRET_KEY sa environment variables
SECRET_KEY = 'django-insecure-uab#656oq2z@qbxzpw13sfo5aycdon9f#yd+))l3pfu#zkqgj!'

DEBUG = True

ALLOWED_HOSTS = ['192.168.1.2', '127.0.0.1', 'localhost']

# 2. APPLICATION DEFINITION
INSTALLED_APPS = [ 
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Inyong App
    'documents', 
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

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
            os.path.join(BASE_DIR, 'documents', 'templates'),
        ], 
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # DITO NAKALAGAY ANG IYONG CONTEXT PROCESSOR PARA SA PENDING COUNTS
                'documents.context_processors.global_user_counts', 
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# 3. DATABASE (MySQL)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'deped_dms_db',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': '127.0.0.1',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# 4. CUSTOM USER & AUTHENTICATION
AUTH_USER_MODEL = 'documents.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard_selector'
LOGOUT_REDIRECT_URL = 'login'

# 5. INTERNATIONALIZATION
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Manila'
USE_I18N = True
USE_TZ = True

# 6. STATIC & MEDIA FILES
STATIC_URL = '/static/'

STATICFILES_DIRS = []
main_static = os.path.join(BASE_DIR, 'static')
app_static = os.path.join(BASE_DIR, 'documents', 'static')

if os.path.exists(main_static):
    STATICFILES_DIRS.append(main_static)
if os.path.exists(app_static):
    STATICFILES_DIRS.append(app_static)

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# 7. EMAIL CONFIGURATION (Gmail SMTP)
# Mahalaga ito para sa Forgot Password/Reset Password logic
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_HOST_USER = 'marvinmedrana6@gmail.com'
EMAIL_HOST_PASSWORD = 'ykqxzuhkdijgzedi' 
DEFAULT_FROM_EMAIL = 'DepEd DMS <marvinmedrana6@gmail.com>'
EMAIL_TIMEOUT = 30 

# 8. MISC
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

MESSAGE_TAGS = {
    messages.DEBUG: 'secondary',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}
# settings.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'marvinmedrana6@gmail.com'
EMAIL_HOST_PASSWORD = 'ykqxzuhkdijgzedi' 

# 3. Napakahalaga: Idagdag ito para malaman ng Gmail kung sino ang sender
DEFAULT_FROM_EMAIL = 'DepEd DMS <marvinmedrana6@gmail.com>'
SERVER_EMAIL = 'marvinmedrana6@gmail.com'