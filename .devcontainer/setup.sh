#!/bin/bash

echo "🚀 Setting up Django development environment..."

# Update system packages
sudo apt-get update

# Install additional system dependencies
sudo apt-get install -y \
    postgresql-client \
    redis-server \
    sqlite3 \
    libpq-dev \
    gcc \
    netcat-openbsd

# Upgrade pip and install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Start PostgreSQL service
echo "🗄️ Starting PostgreSQL..."
sudo service postgresql start

# Start Redis server
echo "🔴 Starting Redis..."
sudo service redis-server start

# Create PostgreSQL database and user
echo "📊 Setting up database..."
sudo -u postgres createdb newsaggregator_db || echo "Database already exists"
sudo -u postgres createuser -s newsaggregator_user || echo "User already exists"
sudo -u postgres psql -c "ALTER USER newsaggregator_user PASSWORD 'newsaggregator_password';" || echo "Password already set"

# Set environment variables for the session
echo "🌍 Setting environment variables..."
echo 'export POSTGRES_HOST=localhost' >> ~/.bashrc
echo 'export POSTGRES_DB=newsaggregator_db' >> ~/.bashrc
echo 'export POSTGRES_USER=newsaggregator_user' >> ~/.bashrc
echo 'export POSTGRES_PASSWORD=newsaggregator_password' >> ~/.bashrc
echo 'export POSTGRES_PORT=5432' >> ~/.bashrc
echo 'export REDIS_HOST=localhost' >> ~/.bashrc
echo 'export REDIS_PORT=6379' >> ~/.bashrc
echo 'export CELERY_BROKER_URL=redis://localhost:6379/0' >> ~/.bashrc
echo 'export CELERY_RESULT_BACKEND=redis://localhost:6379/0' >> ~/.bashrc
echo 'export DJANGO_SETTINGS_MODULE=config.settings' >> ~/.bashrc

# Source the environment variables
source ~/.bashrc

# Run Django migrations
echo "🔄 Running migrations..."
python manage.py migrate || echo "Migration failed - will retry later"

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput || echo "Static files collection failed - will retry later"

# Create directories
mkdir -p media static

echo "✅ Setup complete!"
echo ""
echo "🌟 To start development:"
echo "   python manage.py runserver 0.0.0.0:8000"
echo ""
echo "🔧 To start Celery worker (in another terminal):"
echo "   celery -A news_aggregator worker --loglevel=info"
echo ""
echo "⏰ To start Celery beat (in another terminal):"
echo "   celery -A news_aggregator beat --loglevel=info"