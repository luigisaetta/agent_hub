FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install Python dependencies first to maximize build cache reuse.
COPY requirements.txt /app/requirements.txt
COPY demos/demo6/requirements.txt /app/demos/demo6/requirements.txt
RUN pip install --no-cache-dir -r /app/demos/demo6/requirements.txt

# Copy only runtime files needed by demo6 backend.
COPY common /app/common
COPY demos/demo6 /app/demos/demo6
COPY config.py /app/config.py
COPY config_private.py /app/config_private.py

EXPOSE 8080

CMD ["uvicorn", "demos.demo6.api:app", "--host", "0.0.0.0", "--port", "8080"]
