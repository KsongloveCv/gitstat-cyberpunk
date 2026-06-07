FROM python:3.11-slim

WORKDIR /app
COPY backend-py/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt brotli-asgi

COPY backend-py/ /app/backend-py/
COPY frontend/dist/ /app/frontend/dist/

EXPOSE 12580
CMD ["python", "backend-py/main.py", ".", "--port", "12580", "--no-browser"]
