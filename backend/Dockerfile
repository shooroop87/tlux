FROM python:3.9-slim
# Install dependencies
RUN apt-get update && \
    apt-get install -y gettext && \
    apt-get clean
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir
COPY . .
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "transferslux.wsgi"]
RUN django-admin compilemessages -l ru
RUN django-admin compilemessages -l it
RUN django-admin compilemessages -l es
RUN django-admin compilemessages -l fr