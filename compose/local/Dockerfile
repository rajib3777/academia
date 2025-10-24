 FROM python:3.12-slim

 ENV PYTHONDONTWRITEBYTECODE=1
 ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies (for psycopg2, Pillow, etc.)
RUN echo 'Acquire::Check-Valid-Until "false";' > /etc/apt/apt.conf.d/99-no-check-valid-until \
    && apt-get update && apt-get install -y \ 
    curl \
    libpq-dev gcc \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install dependencies
COPY requirements.txt .
RUN uv pip install --no-cache-dir -r requirements.txt --system

# copy entrypoint.sh
COPY ./.envs/.local/entrypoint.local.sh /entrypoint
RUN sed -i 's/\r//' /entrypoint
RUN chmod +x /entrypoint

# Copy project
COPY . .

# Expose port
EXPOSE 8080

# Run Django
ENTRYPOINT ["/entrypoint"] 