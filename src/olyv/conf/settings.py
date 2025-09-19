"""
Django settings file.

For more information on this file, see:
https://docs.djangoproject.com/en/stable/topics/settings/

For the full list of settings and their values, see:
https://docs.djangoproject.com/en/stable/ref/settings/

For when deploying to a production environment, see:
https://docs.djangoproject.com/en/stable/howto/deployment/checklist/
"""

from pathlib import Path

from olyv.utils import find_project_root

OLYV_SETTINGS_PATH = str(Path(__file__).resolve())

# ------------------------------------------------------------------------------
# Project Directories
# ------------------------------------------------------------------------------

BASE_DIR = find_project_root()
LIB_DIR = BASE_DIR / "lib"
LIB_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------------------
# Allowed Hosts
# ------------------------------------------------------------------------------

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# ------------------------------------------------------------------------------
# 📦 Installed Apps
# https://docs.djangoproject.com/en/stable/ref/settings/#installed-apps
# ------------------------------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_browser_reload",
    "django_ckeditor_5",
    "rest_framework",
    "sass_processor",
    "phonenumber_field",
    "olyv.base",
    "olyv.accounts",
    "olyv.addresses",
    "olyv.lists",
    "olyv.articles",
]

# ------------------------------------------------------------------------------
# 🗄️ Database Configuration
# https://docs.djangoproject.com/en/stable/ref/settings/#databases
# https://docs.djangoproject.com/en/stable/ref/databases/
# ------------------------------------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": LIB_DIR / "db.sqlite3",
    }
}

# ------------------------------------------------------------------------------
# 📧 Email Configuration
# https://docs.djangoproject.com/en/stable/topics/email/
# ------------------------------------------------------------------------------

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_PORT = "587"

# ------------------------------------------------------------------------------
# 🔑 Authentication
# https://docs.djangoproject.com/en/stable/topics/auth/customizing/
# https://docs.djangoproject.com/en/stable/ref/settings/#auth-password-validators
# ------------------------------------------------------------------------------

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ------------------------------------------------------------------------------
# 🧩 Middleware
# https://docs.djangoproject.com/en/stable/ref/middleware/
# ------------------------------------------------------------------------------

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_browser_reload.middleware.BrowserReloadMiddleware",
]

# ------------------------------------------------------------------------------
# 🧾 Templates
# https://docs.djangoproject.com/en/stable/ref/settings/#templates
# ------------------------------------------------------------------------------

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ------------------------------------------------------------------------------
# 📂 Static & Sass Files
# https://docs.djangoproject.com/en/stable/howto/static-files/
# ------------------------------------------------------------------------------

STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "sass_processor.finders.CssFinder",
]

SASS_PRECISION = 8
STATIC_URL = "/lib/static/"
STATIC_ROOT = LIB_DIR / "static"

# ------------------------------------------------------------------------------
# 🖼️ Media Files
# https://docs.djangoproject.com/en/stable/ref/settings/#media-files
# ------------------------------------------------------------------------------

MEDIA_URL = "/lib/media/"
MEDIA_ROOT = LIB_DIR / "media"

# ------------------------------------------------------------------------------
# 🌐 Internationalization
# https://docs.djangoproject.com/en/stable/topics/i18n/
# ------------------------------------------------------------------------------

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Nairobi"
USE_I18N = True
USE_TZ = True

# ------------------------------------------------------------------------------
# 📝 Default Auto Field
# https://docs.djangoproject.com/en/stable/ref/settings/#default-auto-field
# ------------------------------------------------------------------------------

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ------------------------------------------------------------------------------
# 🖋️ CKEditor 5 Configuration
# https://pypi.org/project/django-ckeditor-5/
# ------------------------------------------------------------------------------

CKEDITOR_5_CUSTOM_CSS = "olyv/base/vendors/ckeditor/ckeditor.css"

customColorPalette = [
    {"color": "hsl(4, 90%, 58%)", "label": "Red"},
    {"color": "hsl(340, 82%, 52%)", "label": "Pink"},
    {"color": "hsl(291, 64%, 42%)", "label": "Purple"},
    {"color": "hsl(262, 52%, 47%)", "label": "Deep Purple"},
    {"color": "hsl(231, 48%, 48%)", "label": "Indigo"},
    {"color": "hsl(207, 90%, 54%)", "label": "Blue"},
]

CKEDITOR_5_CONFIGS = {
    "default": {
        "toolbar": {
            "items": [
                "heading",
                "|",
                "bold",
                "italic",
                "link",
                "bulletedList",
                "numberedList",
                "blockQuote",
                "imageUpload",
                "|",
                "fontColor",
                "fontBackgroundColor",
                "|",
                "undo",
                "redo",
            ],
            "shouldNotGroupWhenFull": True,
        },
        "fontColor": {
            "colors": customColorPalette,
            "defaultColor": "hsl(0, 0%, 0%)",
        },
        "fontBackgroundColor": {
            "colors": customColorPalette,
        },
    },
    "extends": {
        "toolbar": {
            "items": [
                "heading",
                "|",
                "outdent",
                "indent",
                "|",
                "bold",
                "italic",
                "link",
                "underline",
                "strikethrough",
                "code",
                "subscript",
                "superscript",
                "highlight",
                "|",
                "codeBlock",
                "sourceEditing",
                "insertImage",
                "bulletedList",
                "numberedList",
                "todoList",
                "|",
                "blockQuote",
                "imageUpload",
                "|",
                "fontSize",
                "fontFamily",
                "fontColor",
                "fontBackgroundColor",
                "mediaEmbed",
                "removeFormat",
                "insertTable",
            ],
            "shouldNotGroupWhenFull": True,
        },
        "image": {
            "toolbar": [
                "imageTextAlternative",
                "|",
                "imageStyle:alignLeft",
                "imageStyle:alignRight",
                "imageStyle:alignCenter",
                "imageStyle:side",
                "|",
            ],
            "styles": ["full", "side", "alignLeft", "alignRight", "alignCenter"],
        },
        "table": {
            "contentToolbar": [
                "tableColumn",
                "tableRow",
                "mergeTableCells",
                "tableProperties",
                "tableCellProperties",
            ],
            "tableProperties": {
                "borderColors": customColorPalette,
                "backgroundColors": customColorPalette,
            },
            "tableCellProperties": {
                "borderColors": customColorPalette,
                "backgroundColors": customColorPalette,
            },
        },
        "heading": {
            "options": [
                {
                    "model": "paragraph",
                    "title": "Paragraph",
                    "class": "ck-heading_paragraph",
                },
                {
                    "model": "heading1",
                    "view": "h1",
                    "title": "Heading 1",
                    "class": "ck-heading_heading1",
                },
                {
                    "model": "heading2",
                    "view": "h2",
                    "title": "Heading 2",
                    "class": "ck-heading_heading2",
                },
                {
                    "model": "heading3",
                    "view": "h3",
                    "title": "Heading 3",
                    "class": "ck-heading_heading3",
                },
            ]
        },
    },
    "list": {
        "properties": {
            "styles": "true",
            "startIndex": "true",
            "reversed": "true",
        }
    },
}
