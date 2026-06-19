FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt \
 && python -c "import flask, google.cloud.firestore, google.cloud.storage; print('build-deps-ok')"

COPY . .

CMD exec gunicorn ${APP_MODULE:-app:app} --bind 0.0.0.0:${PORT} --workers 1 --threads 8 --timeout 0
