BROKER_URL = "amqp://guest:guesttest@localhost:5672//"
CELERY_RESULT_BACKEND = "amqp"
CELERY_IMPORTS = ("reviewbot.processing.tasks", )
