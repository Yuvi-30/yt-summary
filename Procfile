release: python manage.py collectstatic --noinput && python manage.py migrate
web: gunicorn ytfinal.wsgi:application --bind 0.0.0.0:$PORT