# celery config is in a non-standard location
import os
os.environ['CELERY_CONFIG_MODULE'] = 'reviewbot.processing.celeryconfig'
