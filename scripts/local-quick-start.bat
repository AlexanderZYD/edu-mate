@echo off
REM EduMate Local Quick Start Script for Windows
REM Fast setup for local Python development

echo 🚀 EduMate Local Quick Start
echo ============================

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed. Please install Python 3.8+ first.
    pause
    exit /b 1
)

echo ✅ Python is installed

REM Check if required packages are installed
echo 📦 Checking Python packages...
python -c "import flask, flask_mysqldb, werkzeug" >nul 2>&1
if %errorlevel% neq 0 (
    echo 📥 Installing required packages...
    pip install flask flask-mysqldb werkzeug email-validator python-dotenv bcrypt PyJWT gunicorn
    if %errorlevel% neq 0 (
        echo ❌ Failed to install packages. Check your pip installation.
        pause
        exit /b 1
    )
    echo ✅ Packages installed successfully
) else (
    echo ✅ Required packages are already installed
)

REM Select database option
echo.
echo 🎯 Please select database option:
echo 1) Use SQLite (Fastest - No database server needed)
echo 2) Use Docker MySQL (Best for testing)
echo 3) Use existing MySQL (Advanced)
set /p db_choice="Enter your choice (1-3): "

if "%db_choice%"=="1" goto sqlite_setup
if "%db_choice%"=="2" goto mysql_docker_setup
if "%db_choice%"=="3" goto mysql_existing_setup

echo ❌ Invalid choice. Please try again.
goto :eof

:sqlite_setup
echo 🗄️ Setting up SQLite database...
if not exist "uploads" mkdir uploads
if exist "edumate_local.db" (
    echo ℹ️ SQLite database already exists
) else (
    echo 📝 Creating new SQLite database...
    python database/sqlite_init.py
)

echo ⚙️ Setting up environment...
copy ".env.local" ".env" >nul 2>&1

echo 🚀 Starting Flask application...
echo 📱 Access the application at: http://localhost:5000
echo 👤 Default login: admin / admin123
echo.
python app_sqlite.py
goto :eof

:mysql_docker_setup
echo 🐳 Setting up MySQL with Docker...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not installed. Please install Docker or choose SQLite option.
    pause
    exit /b 1
)

echo 📦 Starting MySQL container...
docker-compose -f docker-compose.mysql-only.yml up -d

echo ⏳ Waiting for MySQL to be ready...
timeout /t 15 /nobreak >nul

echo ⚙️ Setting up environment...
copy ".env.local" ".env" >nul 2>&1

echo 🗄️ Initializing database...
python database/init_db.py

echo 🚀 Starting Flask application...
echo 📱 Access the application at: http://localhost:5000
echo 👤 Default login: admin / admin123
echo.
python app.py
goto :eof

:mysql_existing_setup
echo ⚙️ Setting up environment for existing MySQL...
copy ".env.local" ".env" >nul 2>&1
echo.
echo 📝 Please update your .env file with your MySQL connection details:
echo    MYSQL_HOST=localhost
echo    MYSQL_USER=your_mysql_user
echo    MYSQL_PASSWORD=your_mysql_password
echo    MYSQL_DB=edumate_db
echo.
echo 📦 Starting Flask application...
echo 📱 Access the application at: http://localhost:5000
python app.py
goto :eof