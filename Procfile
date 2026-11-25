web: cd backend && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 60
worker: cd backend && celery -A config worker --beat -l info --concurrency 2
