# Specify platform to avoid exec format errors
FROM --platform=linux/amd64 python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV DJANGO_SETTINGS_MODULE config.settings

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies required for psycopg2 (PostgreSQL adapter)
# and other potential libraries.
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    libpq-dev \
    netcat-openbsd \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file first to leverage Docker cache
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the entire Django project into the container
COPY . /app/

# Create necessary directories
RUN mkdir -p /app/static /app/media

# Collect static files for production (important for Gunicorn/Nginx)
# Use || true to prevent build failure if collectstatic fails
RUN python manage.py collectstatic --noinput || true

# Create a non-root user for security
RUN adduser --disabled-password --gecos '' appuser \
    && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose the port your Django application will run on
EXPOSE 8000

# Define the default command to run the application
# This will be overridden by docker-compose commands
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]