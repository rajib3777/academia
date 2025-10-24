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
COPY ./entrypoint /entrypoint
RUN sed -i 's/\r//' /entrypoint
RUN chmod +x /entrypoint

# Copy project
COPY . .

# Expose port
EXPOSE 8001

# Run Django
# CMD ["gunicorn", "classmate.wsgi:application", "--bind", "0.0.0.0:8001"]
# CMD [ "python", "manage.py", "runserver", "0.0.0.0:8001" ]


ENTRYPOINT ["/entrypoint"] 