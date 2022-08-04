import os
from pathlib import Path

from split_settings.tools import include

BASE_DIR = Path(__file__).resolve().parent.parent

include(
    'components/database.py',
    'components/apps.py',
    'components/middleware.py',
    'components/templates.py',
    'components/validators.py',
    'components/logging.py',
)

SECRET_KEY = os.environ.get('SECRET_KEY')
DEBUG = os.environ.get('DEBUG', False) == 'True'
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]']
ROOT_URLCONF = 'example.urls'
WSGI_APPLICATION = 'example.wsgi.application'

CORS_ALLOWED_ORIGINS = ['http://127.0.0.1:8080','http://localhost:8080']
LANGUAGE_CODE = 'ru-RU'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SHELL_PLUS = "ipython"

# ETL
BUNCH_EXTRACT = int(os.environ.get('BUNCH_EXTRACT', 100))
BUNCH_INSERT = int(os.environ.get('BUNCH_INSERT', 100))
SQLITE3_PATH = os.environ.get('SQLITE3_PATH')
ES_SCHEMAS_DIR = os.environ.get('ES_SCHEMAS_DIR')
ES_BASE_URL = f"http://{os.environ.get('ES_HOST')}:{os.environ.get('ES_PORT', 9200)}"