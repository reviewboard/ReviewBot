from __future__ import absolute_import

from celery import Celery


celery = Celery('reviewbot.celery', include=['reviewbot.tasks'])

if __name__ == '__main__':
    celery.start()
