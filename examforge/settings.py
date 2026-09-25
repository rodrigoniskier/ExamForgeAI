import os
from pathlib import Path
import dj_database_url

BASE_DIR=Path(__file__).resolve().parent.parent
DEBUG=os.environ.get("DEBUG","0")=="1"
SECRET_KEY=os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    if DEBUG: SECRET_KEY="development-only-not-for-production"
    else: raise RuntimeError("SECRET_KEY is required when DEBUG=0")
ALLOWED_HOSTS=[x.strip() for x in os.environ.get("ALLOWED_HOSTS","localhost,127.0.0.1").split(",") if x.strip()]
CSRF_TRUSTED_ORIGINS=[x.strip() for x in os.environ.get("CSRF_TRUSTED_ORIGINS","").split(",") if x.strip()]
INSTALLED_APPS=["django.contrib.admin","django.contrib.auth","django.contrib.contenttypes","django.contrib.sessions","django.contrib.messages","django.contrib.staticfiles","bank"]
MIDDLEWARE=["django.middleware.security.SecurityMiddleware","whitenoise.middleware.WhiteNoiseMiddleware","django.contrib.sessions.middleware.SessionMiddleware","django.middleware.common.CommonMiddleware","django.middleware.csrf.CsrfViewMiddleware","django.contrib.auth.middleware.AuthenticationMiddleware","django.contrib.messages.middleware.MessageMiddleware","django.middleware.clickjacking.XFrameOptionsMiddleware"]
ROOT_URLCONF="examforge.urls"
TEMPLATES=[{"BACKEND":"django.template.backends.django.DjangoTemplates","DIRS":[BASE_DIR/"templates"],"APP_DIRS":True,"OPTIONS":{"context_processors":["django.template.context_processors.request","django.contrib.auth.context_processors.auth","django.contrib.messages.context_processors.messages"]}}]
WSGI_APPLICATION="examforge.wsgi.application"
DATABASES={"default":dj_database_url.config(default=f"sqlite:///{BASE_DIR/'examforge.db'}",conn_max_age=60,conn_health_checks=True)}
AUTH_PASSWORD_VALIDATORS=[{"NAME":"django.contrib.auth.password_validation.MinimumLengthValidator","OPTIONS":{"min_length":10}},{"NAME":"django.contrib.auth.password_validation.CommonPasswordValidator"},{"NAME":"django.contrib.auth.password_validation.NumericPasswordValidator"}]
LANGUAGE_CODE="en-us"; TIME_ZONE="UTC"; USE_I18N=True; USE_TZ=True
STATIC_URL="/static/"; STATIC_ROOT=BASE_DIR/"staticfiles"
STORAGES={"default":{"BACKEND":"django.core.files.storage.FileSystemStorage"},"staticfiles":{"BACKEND":"whitenoise.storage.CompressedManifestStaticFilesStorage"}}
DEFAULT_AUTO_FIELD="django.db.models.BigAutoField"
LOGIN_URL="/login/"; LOGIN_REDIRECT_URL="/"; LOGOUT_REDIRECT_URL="/login/"
GEMINI_API_KEY=os.environ.get("GEMINI_API_KEY","").strip()
GEMINI_MODEL=os.environ.get("GEMINI_MODEL","gemini-2.5-flash").strip()
USE_FAKE_AI=os.environ.get("USE_FAKE_AI","0")=="1"
SESSION_COOKIE_HTTPONLY=True; SESSION_COOKIE_SAMESITE="Lax"; CSRF_COOKIE_SAMESITE="Lax"; SECURE_CONTENT_TYPE_NOSNIFF=True; X_FRAME_OPTIONS="DENY"; SECURE_REFERRER_POLICY="no-referrer"
if not DEBUG:
    SESSION_COOKIE_SECURE=True; CSRF_COOKIE_SECURE=True
    SECURE_SSL_REDIRECT=os.environ.get("SECURE_SSL_REDIRECT","1")=="1"
    SECURE_HSTS_SECONDS=int(os.environ.get("SECURE_HSTS_SECONDS","31536000")); SECURE_HSTS_INCLUDE_SUBDOMAINS=True
    SECURE_PROXY_SSL_HEADER=("HTTP_X_FORWARDED_PROTO","https")
