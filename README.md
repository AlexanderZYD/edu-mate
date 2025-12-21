# EduMate - Personalized Learning Companion

A Flask-based web application that provides personalized learning recommendations for Malaysian university students.

## Features

### Core Functionality
- **User Management**: Multi-role authentication (Student, Instructor, Admin)
- **Content Management**: Upload, categorize, and manage learning materials
- **Smart Recommendations**: Rule-based algorithm for personalized content suggestions
- **Feedback System**: User ratings and comments to improve recommendations
- **Progress Tracking**: Monitor learning activities and achievements
- **Admin Dashboard**: System analytics and content management

### Technical Stack
- **Backend**: Python 3.8+ with Flask
- **Database**: MySQL with relational design
- **Frontend**: HTML5, CSS3, JavaScript with Bootstrap 5
- **Authentication**: Session-based with password hashing
- **Analytics**: Chart.js for data visualization

## Project Structure

```
edumate/
├── app.py                 # Main Flask application
├── requirements.txt        # Python dependencies
├── .env                   # Environment variables
├── database/
│   ├── schema.sql         # Database schema
│   └── init_db.py         # Database initialization script
├── routes/                # Flask route blueprints
│   ├── __init__.py
│   ├── auth.py           # Authentication routes
│   ├── user.py           # User management routes
│   ├── content.py        # Content management routes
│   ├── recommendation.py # Recommendation system routes
│   └── admin.py          # Admin panel routes
├── templates/             # Jinja2 HTML templates
│   ├── base.html         # Base template
│   ├── index.html        # Landing page
│   ├── dashboard.html    # User dashboard
│   ├── auth/             # Authentication templates
│   ├── user/             # User profile templates
│   ├── content/          # Content templates
│   ├── recommendation/   # Recommendation templates
│   └── admin/            # Admin panel templates
├── static/               # Static assets
│   ├── css/
│   │   └── style.css    # Custom styles
│   └── js/
│       └── main.js       # Main JavaScript file
└── README.md             # This file
```

## Installation and Setup

### Prerequisites
- Docker and Docker Compose (Recommended)
- OR Python 3.8+ and MySQL 5.7+ (Manual Setup)
- Git

### Option 1: Docker Deployment (Recommended)

#### Quick Start
```bash
# Clone repository
git clone <repository-url>
cd edumate

# Start all services
docker-compose up -d

# Initialize database (first time only)
docker-compose exec web python database/init_db.py

# Access the application
# Web App: http://localhost:5000
# MySQL: localhost:3306
# Redis: localhost:6379
```

#### Development Environment
```bash
# Use development configuration
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f web

# Stop services
docker-compose -f docker-compose.dev.yml down
```

#### Production Environment
```bash
# Build and start with production profile
docker-compose --profile production up -d

# This includes Nginx reverse proxy
# Web App: http://localhost:80
```

#### Docker Commands
```bash
# View running containers
docker-compose ps

# View logs
docker-compose logs -f [service_name]

# Execute commands in container
docker-compose exec web bash
docker-compose exec db mysql -u root -p

# Rebuild image
docker-compose build --no-cache

# Stop and remove containers
docker-compose down -v
```

### Option 2: Manual Setup

#### Prerequisites
- Python 3.8 or higher
- MySQL 5.7 or higher
- pip (Python package manager)

### 1. Clone the Repository
```bash
git clone <repository-url>
cd edumate
```

### 2. Create Virtual Environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
Create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
```

Edit `.env` with your database credentials:
```env
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DB=edumate_db
```

### 5. Initialize Database
```bash
python database/init_db.py
```

### 6. Run the Application
```bash
flask run
```

The application will be available at `http://localhost:5000`

## Default Accounts

After database initialization, you can use:

- **Admin Account**:
  - Username: `admin`
  - Email: `your-admin@edumate.com`
  - Password: `admin123`

## User Roles

### Student
- Browse and search content
- View personalized recommendations
- Track learning progress
- Rate and comment on content
- Manage profile and preferences

### Instructor
- All student privileges
- Upload and manage learning materials
- View content analytics
- Manage content categories

### Administrator
- All instructor privileges
- Manage users (activate/deactivate)
- System analytics and reports
- Content moderation
- System configuration

## Database Schema

### Core Tables
- `users` - User accounts and profiles
- `content` - Learning materials and resources
- `categories` - Content organization
- `user_activities` - Learning progress tracking
- `content_feedback` - User ratings and comments
- `recommendations` - Recommendation system logs
- `user_preferences` - Personalization settings
- `system_logs` - Administrative audit trail

## API Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/register` - User registration
- `GET /auth/logout` - User logout

### Content
- `GET /content/browse` - Browse content with filters
- `GET /content/<id>` - View specific content
- `POST /content/upload` - Upload new content (Instructor/Admin)
- `POST /content/<id>/rate` - Rate content

### Recommendations
- `GET /recommendation/for-you` - Personalized recommendations
- `GET /recommendation/trending` - Trending content
- `GET /recommendation/api/refresh` - Refresh recommendations

### Admin
- `GET /admin/dashboard` - Admin dashboard
- `GET /admin/users` - User management
- `GET /admin/content` - Content management
- `GET /admin/analytics` - System analytics

## Recommendation Algorithm

The system uses a rule-based approach that considers:
- User's interests and preferences
- Content difficulty level
- User's learning history
- Content popularity and ratings
- Category preferences

## Features in Detail

### Smart Recommendations
- Analyzes user behavior and preferences
- Considers learning history and progress
- Updates based on user feedback
- Multiple recommendation strategies

### Progress Tracking
- Activity monitoring
- Learning streaks
- Time spent analytics
- Completion metrics

### Social Features
- User ratings and reviews
- Community feedback
- Content sharing
- Discussion forums (planned)

## Security Features

- Password hashing with Werkzeug
- Session-based authentication
- Input validation and sanitization
- SQL injection prevention
- Cross-site scripting (XSS) protection
- Role-based access control

## Performance Optimization

- Database query optimization
- Lazy loading for large datasets
- Caching frequently accessed data
- Responsive design for mobile devices
- Optimized static asset delivery

## Development Guidelines

### Code Style
- Follow PEP 8 Python standards
- Use descriptive variable names
- Include docstrings for functions
- Implement proper error handling

### Database
- Use parameterized queries
- Implement proper foreign key constraints
- Include timestamps for tracking
- Normalize data where appropriate

### Frontend
- Mobile-first responsive design
- Progressive enhancement
- Accessible HTML markup
- Consistent UI components

## Testing

Run tests with:
```bash
python -m pytest tests/
```

## Deployment

### Production Environment Variables
```env
FLASK_ENV=production
SECRET_KEY=your-production-secret-key
MYSQL_HOST=your-production-db-host
MYSQL_USER=your-production-db-user
MYSQL_PASSWORD=your-production-db-password
MYSQL_DB=edumate_production
```

### Using Gunicorn
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new features
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation

## Acknowledgments

This project is developed for the CAT304W Group Innovation Project at Universiti Sains Malaysia and aligns with UN Sustainable Development Goal 4: Quality Education.