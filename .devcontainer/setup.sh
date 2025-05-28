#!/bin/bash

echo "🚀 Setting up Python environment..."

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt || echo "No requirements.txt or install failed"

# Create media/static dirs
mkdir -p media static

# Run migrations and collectstatic
echo "🔄 Running Django migrations..."
python manage.py migrate || echo "Migration failed"

echo "📁 Collecting static files..."
python manage.py collectstatic --noinput || echo "Static collection failed"

echo "✅ Setup complete"

echo "🛠 Installing Redis..."
sudo apt update
sudo apt install -y redis-server || echo "Redis installation failed"

echo "🚀 Starting Redis service..."
sudo service redis-server start || echo "Failed to start Redis"
# Start the Django development server