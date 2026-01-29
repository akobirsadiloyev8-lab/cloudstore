# Base image - Python va LibreOffice bilan
FROM python:3.12-slim

# LibreOffice va kerakli paketlarni o'rnatish
RUN apt-get update && apt-get install -y \
    libreoffice \
    libreoffice-writer \
    libreoffice-calc \
    libreoffice-impress \
    fonts-liberation \
    fonts-dejavu \
    fonts-freefont-ttf \
    fonts-noto \
    fonts-noto-cjk \
    fonts-noto-color-emoji \
    fontconfig \
    libpq-dev \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Shriftlarni yangilash
RUN fc-cache -f -v

# Working directory
WORKDIR /app

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Static fayllarni yig'ish
RUN python manage.py collectstatic --noinput

# Media papkasini yaratish
RUN mkdir -p /app/media/files /app/media/images /app/media/books /app/media/authors /app/media/book_covers

# Port
EXPOSE 8000

# Start script yaratish - migrate va gunicorn
RUN echo '#!/bin/bash\necho "Running migrations..."\npython manage.py migrate --noinput\necho "Starting server..."\ngunicorn --bind 0.0.0.0:8000 --workers 2 --timeout 120 mysite.wsgi:application' > /app/start.sh && chmod +x /app/start.sh

# Gunicorn bilan ishga tushirish (migrate bilan)
CMD ["/app/start.sh"]
