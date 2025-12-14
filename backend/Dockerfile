FROM python:3.9-slim-bookworm

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

# 3) компиляция переводов (best effort)
RUN django-admin compilemessages -l ru -l it -l es -l fr || true

# 4) каталог для статики
RUN mkdir -p /app/collected_static

# 5) entrypoint
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

# <<< ВАЖНО: теперь entrypoint реально будет выполняться >>>
ENTRYPOINT ["/app/entrypoint.sh"]

CMD ["gunicorn", "transferslux.wsgi:application", "--bind", "0.0.0.0:8000", "--workers=1", "--threads=2", "--timeout=120"]