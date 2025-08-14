# backend/Dockerfile
FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# gettext нужен для compilemessages
RUN apt-get update && \
    apt-get install -y --no-install-recommends gettext && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 1) зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2) код проекта
COPY . .

# 3) компиляция переводов (если локали есть; не валимся, если их нет)
RUN django-admin compilemessages -l ru -l it -l es -l fr || true

# 4) каталог для собранной статики (совпадает с STATIC_ROOT)
RUN mkdir -p /app/collected_static

# 5) entrypoint: ждём БД, migrate, collectstatic
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

# CMD можно оставить — в docker-compose мы его переопределяем через `command:`
CMD ["gunicorn", "transferslux.wsgi:application", "--bind", "0.0.0.0:8000", "--workers=3"]
