# ── Stage 1: Build frontend ──
FROM node:22-slim AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ .
RUN npm run build

# ── Stage 2: Runtime ──
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends git curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend-py/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend-py/ /app/backend-py/
COPY --from=frontend /frontend/dist/ /app/frontend/dist/

RUN useradd -m -u 1000 gitstat && \
    mkdir -p /home/gitstat/.gitstat /home/gitstat/.gitstat-gitee-cache /home/gitstat/.hermes \
    && chown -R gitstat:gitstat /home/gitstat

VOLUME /home/gitstat/.gitstat /home/gitstat/.gitstat-gitee-cache

EXPOSE 12580
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://127.0.0.1:12580/health || exit 1

USER gitstat
CMD ["python", "backend-py/main.py", "/data", "--host", "0.0.0.0", "--port", "12580", "--no-browser"]