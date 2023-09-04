web: gunicorn --worker-class eventlet -w 1 app:app
worker: python -m celery -A app.celery worker --loglevel=info