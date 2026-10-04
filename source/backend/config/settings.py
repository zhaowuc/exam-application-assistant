"""Offline-first Django settings shared by source and portable executable."""
import os
import secrets
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent
RESOURCE_DIR = Path(os.environ.get('EXAM_RESOURCE_DIR', BASE_DIR))
DATA_DIR = Path(os.environ.get('EXAM_DATA_DIR', BASE_DIR.parent / 'data'))
DATA_DIR.mkdir(parents=True, exist_ok=True)
secret_file = DATA_DIR / '.secret'
if not secret_file.exists():
    try:
        with secret_file.open('x', encoding='utf-8') as out:
            out.write(secrets.token_urlsafe(48))
    except FileExistsError:
        pass
SECRET_KEY = secret_file.read_text(encoding='utf-8').strip()
DEBUG = os.environ.get('EXAM_DEBUG') == '1'
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'testserver']
INSTALLED_APPS = [
    'django.contrib.auth', 'django.contrib.contenttypes', 'django.contrib.sessions',
    'django.contrib.staticfiles', 'rest_framework',
    'rest_framework_simplejwt.token_blacklist', 'core.apps.CoreConfig',
]
MIDDLEWARE = [
    'services.operations.DatabaseGuard',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'
AUTH_USER_MODEL = 'core.User'
DATABASES = {'default': {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': os.environ.get('EXAM_DB', DATA_DIR / 'db.sqlite3'),
    'OPTIONS': {'timeout': 20},
}}
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
]
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ['core.security.VersionedAuthentication'],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
    'DEFAULT_PAGINATION_CLASS': 'core.common.Pagination',
    'PAGE_SIZE': 12,
    'DEFAULT_RENDERER_CLASSES': ['core.common.EnvelopeRenderer'],
    'EXCEPTION_HANDLER': 'core.common.exception_handler',
}
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
CSRF_COOKIE_SAMESITE = 'Strict'
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
FILE_UPLOAD_MAX_MEMORY_SIZE = 8 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
