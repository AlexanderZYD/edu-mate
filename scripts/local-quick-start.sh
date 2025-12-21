#!/bin/bash

# EduMate Local Quick Start Script for Linux/macOS
# Fast setup for local Python development

set -e

echo "🚀 EduMate Local Quick Start"
echo "============================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

echo "✅ Python is installed"

# Check if required packages are installed
echo "📦 Checking Python packages..."
python3 -c "import flask, flask_mysqldb, werkzeug" 2>/dev/null || {
    echo "📥 Installing required packages..."
    pip3 install flask flask-mysqldb werkzeug email-validator python-dotenv bcrypt PyJWT gunicorn
    echo "✅ Packages installed successfully"
} && {
    echo "✅ Required packages are already installed"
}

# Select database option
echo ""
echo "🎯 Please select database option:"
echo "1) Use SQLite (Fastest - No database server needed)"
echo "2) Use Docker MySQL (Best for testing)"
echo "3) Use existing MySQL (Advanced)"
read -p "Enter your choice (1-3): " db_choice

case $db_choice in
    1)
        sqlite_setup
        ;;
    2)
        mysql_docker_setup
        ;;
    3)
        mysql_existing_setup
        ;;
    *)
        echo "❌ Invalid choice. Please try again."
        exit 1
        ;;
esac

sqlite_setup() {
    echo "🗄️ Setting up SQLite database..."
    
    # Create uploads directory
    mkdir -p uploads
    
    # Create SQLite database if it doesn't exist
    if [ ! -f "edumate_local.db" ]; then
        echo "📝 Creating new SQLite database..."
        python3 database/sqlite_init.py
    else
        echo "ℹ️ SQLite database already exists"
    fi
    
    # Setup environment
    echo "⚙️ Setting up environment..."
    cp .env.local .env
    
    echo "🚀 Starting Flask application..."
    echo "📱 Access the application at: http://localhost:5000"
    echo "👤 Default login: admin / admin123"
    echo ""
    python3 app_sqlite.py
}

mysql_docker_setup() {
    echo "🐳 Setting up MySQL with Docker..."
    
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker is not installed. Please install Docker or choose SQLite option."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo "❌ Docker Compose is not installed. Please install Docker Compose."
        exit 1
    fi
    
    echo "📦 Starting MySQL container..."
    docker-compose -f docker-compose.mysql-only.yml up -d
    
    echo "⏳ Waiting for MySQL to be ready..."
    sleep 15
    
    # Check if MySQL is ready
    max_attempts=10
    attempt=1
    while [ $attempt -le $max_attempts ]; do
        if docker-compose -f docker-compose.mysql-only.yml exec -T mysql mysqladmin ping -h localhost -u edumate_user -pedumate_password --silent; then
            echo "✅ MySQL is ready!"
            break
        fi
        echo "⏳ Waiting for MySQL... (attempt $attempt/$max_attempts)"
        sleep 3
        attempt=$((attempt + 1))
    done
    
    # Setup environment
    echo "⚙️ Setting up environment..."
    cp .env.local .env
    
    echo "🗄️ Initializing database..."
    python3 database/init_db.py
    
    echo "🚀 Starting Flask application..."
    echo "📱 Access the application at: http://localhost:5000"
    echo "👤 Default login: admin / admin123"
    echo ""
    python3 app.py
}

mysql_existing_setup() {
    echo "⚙️ Setting up environment for existing MySQL..."
    cp .env.local .env
    
    echo ""
    echo "📝 Please update your .env file with your MySQL connection details:"
    echo "   MYSQL_HOST=localhost"
    echo "   MYSQL_USER=your_mysql_user"
    echo "   MYSQL_PASSWORD=your_mysql_password"
    echo "   MYSQL_DB=edumate_db"
    echo ""
    
    # Prompt user to continue
    read -p "Press Enter after updating your .env file..."
    
    echo "🗄️ Initializing database..."
    python3 database/init_db.py
    
    echo "🚀 Starting Flask application..."
    echo "📱 Access the application at: http://localhost:5000"
    python3 app.py
}