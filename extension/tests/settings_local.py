import os
import reviewboard


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
    }
}

PRODUCTION = False
DEBUG = True
LOCAL_ROOT = os.path.dirname(reviewboard.__file__)

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
    },
}

SECRET_KEY = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWX'
