# Use ARM64-compatible Python slim image
FROM --platform=linux/arm64 python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies (for psycopg2, Pillow, etc.)
RUN apt-get update && apt-get install -y \ 
    curl \
    libpq-dev gcc \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install dependencies
COPY requirements.txt .
RUN uv pip install --no-cache-dir -r requirements.txt --system

# copy entrypoint.sh
COPY ./.envs/.production/entrypoint.production.sh /entrypoint
RUN sed -i 's/\r//' /entrypoint
RUN chmod +x /entrypoint

# Copy project
COPY . .

# Expose port
EXPOSE 80

# Run Django
ENTRYPOINT ["/entrypoint"] 