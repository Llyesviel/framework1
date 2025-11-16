FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY backend /app/backend

ENV DJANGO_SETTINGS_MODULE=config.settings

RUN python backend/manage.py collectstatic --noinput || true

CMD ["gunicorn", "config.wsgi:application", "--chdir", "backend", "-b", "0.0.0.0:8000"]