# settings.py

from pathlib import Path
import os
import re
import logging, os
from pathlib import Path
from dotenv import load_dotenv          # pip install python-dotenv

# 🔧 load .env from the backend directory
backend_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
print(f"Loading .env from: {backend_env_path}")
load_dotenv(dotenv_path=backend_env_path)
logger = logging.getLogger(__name__)

DJANGO_ENV = os.environ.get('DJANGO_ENV', 'Did you forget to set DJANGO_ENV?')

# 🚀 OpenAI官方API配置 - 纯净GPT-5实现
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")   # OpenAI API key
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5")  # 默认使用GPT-5

if OPENAI_API_KEY:
    logger.info("🚀 OpenAI API configured - GPT-5 available!")
else:
    logger.warning("OPENAI_API_KEY missing – CookAI will run in stub mode.")

BASE_DIR = Path(__file__).resolve().parent.parent

# SECRET_KEY comes from the environment. Never hardcode it here: a key in the
# source is readable by everyone who can read the repository.
#   python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured(
        "DJANGO_SECRET_KEY is not set. Add it to backend/.env "
        "(see backend/.env.example)."
    )

# DEBUG defaults to off. It was previously hardcoded to True, which exposes
# configuration and environment variables on error pages.
DEBUG = os.getenv("DEBUG", "false").strip().lower() in ("1", "true", "yes", "on")

# 🔧 改善：环境变量化的主机配置
def env(name: str, default: str = "") -> str:
    """os.getenv, but an empty value counts as unset.

    .env files routinely carry `KEY=` for "not configured yet"; os.getenv then
    returns "" and skips the default, which produced malformed origins such as
    "https://" further down.
    """
    return (os.environ.get(name) or "").strip() or default


PRODUCTION_HOST = env("PRODUCTION_HOST")
if DJANGO_ENV == "prod" and not PRODUCTION_HOST:
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured(
        "PRODUCTION_HOST must be set when DJANGO_ENV=prod; "
        "ALLOWED_HOSTS and CORS origins are derived from it."
    )
LOCAL_HTTPS_HOST = env("LOCAL_HTTPS_HOST", "localhost")
FRONTEND_PORT = env("FRONTEND_PORT", "520")
BACKEND_PORT = env("BACKEND_PORT", "911")
HTTPS_PORT = env("HTTPS_PORT", "5200")

ALLOWED_HOSTS = [
    PRODUCTION_HOST,
    LOCAL_HTTPS_HOST,
    'localhost', 
    '127.0.0.1',
    'web',
    'web-dev',
    'testserver'  
]

# ────────────────────────────────────────────────────────────
# Feature toggles / gameplay knobs
# ────────────────────────────────────────────────────────────
# Daily check-in / slot machine cooldown hours
# Default: prod=1 hour, non-prod=0 (for quicker QA)
try:
    _default_cooldown = 1 if os.getenv('DJANGO_ENV', 'dev') == 'prod' else 0
    CHECKIN_COOLDOWN_HOURS = int(os.getenv('CHECKIN_COOLDOWN_HOURS', str(_default_cooldown)))
except Exception:
    CHECKIN_COOLDOWN_HOURS = 1

# Optional: Admin gating for check-in by user id or username (comma separated)
_block_ids = os.getenv('CHECKIN_BLOCKLIST_IDS', '')
_block_usernames = os.getenv('CHECKIN_BLOCKLIST_USERNAMES', '')
CHECKIN_BLOCKLIST_IDS = {x.strip() for x in _block_ids.split(',') if x.strip()}
CHECKIN_BLOCKLIST_USERNAMES = {x.strip() for x in _block_usernames.split(',') if x.strip()}

# SMS Settings
TEXTBELT_API_KEY = os.environ.get('TEXTBELT_API_KEY')
SMS_MAX_RETRIES = 3
SMS_RETRY_DELAY = 1.0
OTP_EXPIRY_MINUTES = 60  # OTP有效期
OTP_MAX_ATTEMPTS = 3     # 最大验证次数

INSTALLED_APPS = [
    'avatar',
    'users',
    'system',  # 🔧 System configuration - must be before business apps
    'analytics',  # 📊 User behavior analytics - AAA-grade tracking system
    'cookai',
    'recipes',
    'jazzmin',
    'import_export',
    # 'admin_action_tools',
    # 'admin_searchable_dropdown',
    # 'advanced_filters',
    'petcare',
    'sms_service',
    'couplememory',
    'django_extensions',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',           # <— add this
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'analytics.middleware.AnalyticsMiddleware',  # 📊 Automatic user behavior tracking
]

ROOT_URLCONF = 'app.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'app.wsgi.application'

print(f"***DJANGO_ENV***: {DJANGO_ENV}")

if DJANGO_ENV == 'prod':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('POSTGRES_DB', 'your_db_name'),
            'USER': os.environ.get('POSTGRES_USER', 'your_db_user'),
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'your_db_password'),
            'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
            'PORT': os.environ.get('POSTGRES_PORT', '19777'),
        }
    }
else:
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

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/New_York'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [ BASE_DIR / "static" ]
STATIC_ROOT = BASE_DIR / "staticfiles"

# 生产环境静态文件配置
if DJANGO_ENV == 'prod':
    STATIC_URL = '/static/'
    # nginx serves static files in production, so Django does not
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / "media"
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'users.CustomUser'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {'format': '[{asctime}] {levelname} {name} {message}', 'style': '{'},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'verbose'},
    },
    'root': {'handlers': ['console'], 'level': 'INFO'},
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',  # ← 新增
        'rest_framework.authentication.TokenAuthentication',          # 仍保留原 TokenAuth 兼容旧客户端
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

from datetime import timedelta

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=3),      # 访问令牌 3 小时（3小时不活动后需要刷新）
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),      # 刷新令牌 7 天（7天内免登录）
    "ROTATE_REFRESH_TOKENS": True,                    # 自动旋转刷新令牌
    "BLACKLIST_AFTER_ROTATION": True,                 # 旧刷新令牌失效
    "AUTH_HEADER_TYPES": ("Bearer",),                 # 前端发送：Authorization: Bearer <token>
}

# 🔧 改善：动态生成的跨域配置
_WHITELIST_CANDIDATES = [
    # 生产环境 - 前端和后端端口
    f"http://{PRODUCTION_HOST}:{FRONTEND_PORT}",
    f"https://{PRODUCTION_HOST}:{FRONTEND_PORT}",
    f"https://{PRODUCTION_HOST}:{BACKEND_PORT}",  # backend HTTPS port
    f"https://{PRODUCTION_HOST}:{HTTPS_PORT}",   # 🆕 新增：HTTPS统一入口端口5200
    f"https://{PRODUCTION_HOST}",
    # 本地开发环境
    f"http://{LOCAL_HTTPS_HOST}:{FRONTEND_PORT}",
    f"https://{LOCAL_HTTPS_HOST}:{HTTPS_PORT}",
    f"https://{LOCAL_HTTPS_HOST}:{BACKEND_PORT}",  # 本地backend HTTPS port
    f"https://{LOCAL_HTTPS_HOST}",
    f"http://localhost:{FRONTEND_PORT}",
    f"https://localhost:{HTTPS_PORT}",
    f"https://localhost:{BACKEND_PORT}",  # localhostbackend HTTPS port
    f"https://localhost",
    f"http://127.0.0.1:{FRONTEND_PORT}",
    f"https://127.0.0.1:{HTTPS_PORT}",
    f"https://127.0.0.1:{BACKEND_PORT}",  # 127.0.0.1backend HTTPS port
    # Docker 内部通信
    f"http://web:{BACKEND_PORT}",
    f"http://web-dev:{BACKEND_PORT}",
    f"http://frontend:{FRONTEND_PORT}",
    f"http://frontend-dev:{FRONTEND_PORT}",
]

# Drop any origin whose host is missing — PRODUCTION_HOST is empty until it is
# configured, and corsheaders rejects the whole settings module over one
# malformed entry (E013).
WHITELIST = [
    o for o in _WHITELIST_CANDIDATES
    if re.match(r"^https?://[A-Za-z0-9.\-]+(?::\d+)?$", o)
]

CORS_ALLOWED_ORIGINS = WHITELIST
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = WHITELIST

# CSRF和Session cookie配置（基于环境）
CSRF_COOKIE_SAMESITE = 'None'  # 支持跨站请求
SESSION_COOKIE_SAMESITE = 'None'  # 支持跨站请求
CSRF_COOKIE_SECURE = True if os.getenv('USE_HTTPS') == 'true' else False
SESSION_COOKIE_SECURE = True if os.getenv('USE_HTTPS') == 'true' else False

# in production CORS_ALLOW_ALL_ORIGINS is off and the whitelist applies
CORS_ALLOW_ALL_ORIGINS = False if os.getenv('USE_HTTPS') == 'true' else True

# HTTPS 安全设置
if os.getenv('USE_HTTPS') == 'true':
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = False  # 由Nginx处理重定向
    USE_TLS = True
    SECURE_HSTS_SECONDS = 31536000  # 1年
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'

# CORS 允许的头部
CORS_ALLOW_HEADERS = [
    'content-type',
    'authorization',
    'cache-control',  # Add 'Cache-Control' here
    'x-requested-with',
    'accept',
    'origin',
    'x-csrftoken',
]
# ────────────────────────────────────────────────────────────
# Jazzmin settings (unchanged from before)
# ────────────────────────────────────────────────────────────
JAZZMIN_SETTINGS = {
    "site_title": "PlateMate Admin",
    "site_header": "PlateMate",
    "site_brand": "PlateMate",
    "site_logo": "images/logo.png",
    "login_logo": "images/login_logo.png",
    "site_icon": "platemate.ico",
    "welcome_sign": "Welcome to PlateMate Admin",
    "copyright": "PlateMate from Eclipzion",
    "show_ui_builder": True,
    "search_model": "auth.User",
    "show_sidebar": True,
    "navigation_expanded": True,
    "changeform_format": "vertical_tabs",
    "changeform_format_overrides": {"auth.user": "collapsible"},
    "language_chooser": True,
    "custom_css": "css/custom_admin.css",
    "custom_js": "js/custom_admin.js",
    "order_with_respect_to": [
        "auth",
        "auth.User",
        "auth.Group",
        "users",
        "recipes",
        "petcare",
    ],
    "icons": {
        "auth": "fas fa-lock",
        "auth.User": "fas fa-user",
        "users.CustomUser": "fas fa-id-badge",
        "recipes.Recipe": "fas fa-book-open",
        "petcare.Pet": "fas fa-paw",
    },
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    "custom_links": {
        "": [   # top‐level global links
            {
                "name":        "OpenAI Playground",
                "url":         "/admin/cookai/openai-test/",
                "icon":        "fas fa-robot",
                "permissions": ["cookai.view_aiprompt"],
            },
        ],
    },
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": True,
    "brand_small_text": False,
    "brand_colour": "navbar-pink",
    "accent": "accent-lightblue",
    "navbar": "navbar-white navbar-light",
    "no_navbar_border": False,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": True,
    "sidebar_fixed": True,
    "sidebar": "sidebar-light-fuchsia",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": True,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": True,
    "theme": "sandstone",
    "dark_mode_theme": "superhero",
    "button_classes": {
        "primary": "btn-outline-primary",
        "secondary": "btn-outline-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    },
    "actions_sticky_top": False
}

# ────────────────────────────────────────────────────────────
# modeladmin-reorder config (unchanged)
# ────────────────────────────────────────────────────────────
MODELADMIN_REORDER = [
    {"app": "auth",    "models": ["auth.User", "auth.Group"]},
    {"app": "users",   "label": "User Management",   "models": ["users.CustomUser"]},
    {"app": "recipes", "label": "Recipe Management", "models": ["recipes.Recipe", "recipes.Ingredient"]},
    {"app": "petcare", "label": "Pet Care",          "models": ["petcare.Pet"]},
]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
# django-import-export 配置
IMPORT_EXPORT_USE_TRANSACTIONS = True
# django-advanced-filters 配置
ADVANCED_FILTERS_EDIT_BY_USER = True

# 🔒 最小HTTPS支持 (移动设备定位权限)
if os.getenv('USE_HTTPS') == 'true':
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

# 📸 文件上传配置 (支持大图片和AI处理)
FILE_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000

# 🤖 AI处理超时配置
if DJANGO_ENV == 'prod':
    # 生产环境使用更长的超时时间
    OPENAI_TIMEOUT = 300  # 5分钟
else:
    # 开发环境使用较短的超时时间
    OPENAI_TIMEOUT = 120  # 2分钟