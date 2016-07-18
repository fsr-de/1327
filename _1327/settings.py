"""
Django settings for _1327 project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
from datetime import timedelta
import os

BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "_1327")

AUTH_USER_MODEL = 'user_management.UserProfile'

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'usba$w)n_sr3u(u1os05!8t6)m(w0skpx&%n@wwpgi_bzdxt-e'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

DELETE_EMPTY_PAGE_AFTER = timedelta(hours=1)

FORBIDDEN_URLS = ["admin", "login", "logout", "documents", "minutes", "polls"]

ANONYMOUS_GROUP_NAME = "Anonymous"
STAFF_GROUP_NAME = "Staff"
UNIVERSITY_GROUP_NAME = "University Network"


# Application definition

INSTALLED_APPS = [
	'django_admin_bootstrapped',
	'django.contrib.admin',
	'django.contrib.auth',
	'django.contrib.contenttypes',
	'django.contrib.sessions',
	'django.contrib.messages',
	'django.contrib.staticfiles',
	'static_precompiler',
	'bootstrap3',
	'reversion',
	'guardian',
	'polymorphic',
	'_1327.main',
	'_1327.user_management',
	'_1327.documents',
	'_1327.information_pages',
	'_1327.minutes',
	'_1327.polls',
]

MIDDLEWARE_CLASSES = [
	'django.contrib.sessions.middleware.SessionMiddleware',
	'django.middleware.common.CommonMiddleware',
	'django.middleware.csrf.CsrfViewMiddleware',
	'django.contrib.auth.middleware.AuthenticationMiddleware',
	'django.contrib.messages.middleware.MessageMiddleware',
	'django.middleware.clickjacking.XFrameOptionsMiddleware',
	'django.middleware.locale.LocaleMiddleware',
]

AUTHENTICATION_BACKENDS = [
	'django.contrib.auth.backends.ModelBackend',
	'guardian.backends.ObjectPermissionBackend',
]

# needed by django-guardian library
ANONYMOUS_USER_ID = -1
GUARDIAN_RAISE_403 = True

BOOTSTRAP3 = {
	'horizontal_label_class': 'col-md-2',
	'horizontal_field_class': 'col-md-9',
}

DAB_FIELD_RENDERER = 'django_admin_bootstrapped.renderers.BootstrapFieldRenderer'

ROOT_URLCONF = '_1327.urls'

WSGI_APPLICATION = '_1327.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
	'default': {
		'ENGINE': 'django.db.backends.sqlite3',
		'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
	}
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'de-DE'
ACTIVE_LANGUAGE = 'de'

TIME_ZONE = 'Europe/Berlin'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LOGIN_URL = '/login'
LOGOUT_URL = '/logout'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/opt/_1327/_1327/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# Absolute path to the directory user uploaded files (like pdf and png) should be put in.
# Example: "/opt/_1327/_1327/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# the Backend used for downloading attachments may be one of the following:
# `sendfile.backends.development` - for use with django development server only. DO NOT USE IN PRODUCTION
# `sendfile.backends.simple` - "simple" backend that uses Django file objects to attempt to stream files from disk
# 	(note middleware may cause files to be loaded fully into memory)
# `sendfile.backends.xsendfile` - sets X-Sendfile header (as used by mod_xsendfile/apache and lighthttpd)
# `sendfile.backends.mod_wsgi` - sets Location with 200 code to trigger internal redirect (daemon mode mod_wsgi only - see below)
# `sendfile.backends.nginx` - sets X-Accel-Redirect header to trigger internal redirect to file
# see https://github.com/johnsensible/django-sendfile for further information
SENDFILE_BACKEND = 'sendfile.backends.development'

# Additional locations of static files
STATICFILES_DIRS = [
	os.path.join(BASE_DIR, "static"),
]

STATICFILES_FINDERS = [
	'django.contrib.staticfiles.finders.FileSystemFinder',
	'django.contrib.staticfiles.finders.AppDirectoriesFinder',
	'static_precompiler.finders.StaticPrecompilerFinder',
]

SUPPORTED_IMAGE_TYPES = ["jpg", "jpeg", "png", "gif", "tiff", "bmp"]

TEMPLATES = [
	{
		'BACKEND': 'django.template.backends.django.DjangoTemplates',
		'DIRS': [
			os.path.join(BASE_DIR, "templates"),
		],
		'APP_DIRS': True,
		'OPTIONS': {
			'context_processors': [
				'django.contrib.auth.context_processors.auth',
				'django.template.context_processors.debug',
				'django.template.context_processors.i18n',
				'django.template.context_processors.media',
				'django.template.context_processors.request',
				'django.template.context_processors.static',
				'django.template.context_processors.tz',
				'django.contrib.messages.context_processors.messages',
				'_1327.main.context_processors.set_language',
				'_1327.main.context_processors.menu',
				'_1327.main.context_processors.can_create_informationpage',
				'_1327.main.context_processors.can_create_minutes',
				'_1327.main.context_processors.can_create_poll',
			],
		},
	},
]

STATIC_PRECOMPILER_COMPILERS = [
	'static_precompiler.compilers.CoffeeScript',
	'static_precompiler.compilers.LESS',
]

# Set this to the ID of the document that shall be shown as Main Page
MAIN_PAGE_ID = -1

# Create a localsettings.py to override settings per machine or user, e.g. for
# development or different settings in deployments using multiple servers.
_LOCAL_SETTINGS_FILENAME = os.path.join(BASE_DIR, "localsettings.py")
if os.path.exists(_LOCAL_SETTINGS_FILENAME):
	exec(compile(open(_LOCAL_SETTINGS_FILENAME, "rb").read(), _LOCAL_SETTINGS_FILENAME, 'exec'))
del _LOCAL_SETTINGS_FILENAME
