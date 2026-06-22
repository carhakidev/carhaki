FROM python:3.12-slim

# System dependencies (WeasyPrint requires Cairo, Pango)
RUN apt-get update && apt-get install -y \
    libcairo2 libpango-1.0-0 libpangocairo-1.0-0 \
    libgdk-pixbuf-xlib-2.0-0 libffi-dev shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput --settings=carhaki.settings.production

EXPOSE 8000

CMD ["gunicorn", "carhaki.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120"]
