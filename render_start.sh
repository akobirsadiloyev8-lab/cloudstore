# Render.com uchun sozlamalar

# Build command
# pip install -r requirements.txt && python manage.py collectstatic --noinput

# Start command (gunicorn)
gunicorn mysite.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
