import os

class Config:
    # Celery:
    CELERY_BROKER_URL = os.environ.get('REDIS_URL')
    CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL')
    # Redis:
    REDIS_URL = os.environ.get('REDIS_URL')