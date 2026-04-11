FROM python:3.12-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install Python dependencies first to maximize build cache reuse.
COPY requirements.txt /app/requirements.txt
COPY agents/hello_world/requirements.txt /app/agents/hello_world/requirements.txt
RUN pip install --no-cache-dir -r /app/agents/hello_world/requirements.txt

# Copy only runtime files needed by hello_world backend.
COPY agents/hello_world /app/agents/hello_world

EXPOSE 8080

CMD ["uvicorn", "agents.hello_world.api:app", "--host", "0.0.0.0", "--port", "8080"]
