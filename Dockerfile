FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend-py/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt brotli-asgi

COPY backend-py/ /app/backend-py/
COPY frontend/dist/ /app/frontend/dist/

RUN useradd -m -u 1000 gitstat
USER gitstat

EXPOSE 12580
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:12580/health')" || exit 1

CMD ["python", "backend-py/main.py", "/data", "--host", "0.0.0.0", "--port", "12580", "--no-browser"]
