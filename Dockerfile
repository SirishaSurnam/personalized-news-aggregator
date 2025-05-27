# Specify platform to avoid exec format errors
FROM --platform=linux/amd64 python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
# Fix: Use consistent settings module name
ENV DJANGO_SETTINGS_MODULE news_aggregator.settings

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

# Create necessary directories and set permissions
RUN mkdir -p /app/static /app/media

# Make entrypoint script executable
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# DON'T switch to non-root user for Codespaces compatibility
# Codespaces handles user management differently
# USER appuser

# Expose the port your Django application will run on
EXPOSE 8000

# Define the default command to run the application
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]