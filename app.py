"""
EduMate - Personalized Learning Companion
Main Flask Application
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import sqlite3
import logging
from datetime import datetime
from config import config

# Load configuration
config_name = 'development'  # Change this to 'production' for production
app = Flask(__name__)
app.config.from_object(config[config_name])

def get_db_connection():
    """Get database connection"""
    try:
        conn = sqlite3.connect('edumate_local.db')
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return conn
    except Exception as err:
        flash(f'Database error: {err}', 'error')
        return None

# Setup logging for debugging
if app.config.get('DEBUG'):
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s'
    )
    app.logger.debug('Debug mode enabled')

# Import route blueprints
from routes.auth import auth_bp
from routes.user import user_bp
from routes.content import content_bp
from routes.recommendation import recommendation_bp
from routes.admin import admin_bp

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(user_bp, url_prefix='/user')
app.register_blueprint(content_bp, url_prefix='/content')
app.register_blueprint(recommendation_bp, url_prefix='/recommend')
app.register_blueprint(admin_bp, url_prefix='/admin')

@app.route('/')
def index():
    """Home page - EduMate landing page - same for all users"""
    # Get user info for template if logged in
    connection = get_db_connection()
    if not connection:
        return render_template('index.html', user=None, featured_content=[])
    
    user = None
    featured_content = []
    
    try:
        if 'user_id' in session:
            # Get user information for personalized welcome
            user = connection.execute(
                "SELECT * FROM users WHERE id = ?",
                (session['user_id'],)
            ).fetchone()
            
            # Get some featured content for logged-in users
            featured_content = connection.execute("""
                SELECT c.* FROM content c 
                WHERE c.is_published = 1 
                ORDER BY RANDOM() 
                LIMIT 6
            """).fetchall()
        
        # Always render the index page (don't redirect)
        return render_template('index.html', user=user, featured_content=featured_content)
    
    except Exception as e:
        flash('Error loading home page', 'error')
        return render_template('index.html', user=None, featured_content=[])
    finally:
        if connection:
            connection.close()



@app.route('/dashboard')
def dashboard():
    """Main dashboard for students only"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    # Only allow students to access the dashboard
    if session.get('user_role') != 'student':
        flash('Access denied. Dashboard is only available for students.', 'error')
        # Redirect based on user role
        if session.get('user_role') == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif session.get('user_role') == 'instructor':
            return redirect(url_for('user.profile'))
        else:
            return redirect(url_for('index'))
    
    connection = get_db_connection()
    if not connection:
        return render_template('dashboard.html', user=None, recent_activities=[])
    
    try:
        # Get user information
        user = connection.execute(
            "SELECT * FROM users WHERE id = ?",
            (session['user_id'],)
        ).fetchone()
        
        # Get recent activities based on user role
        if user and user['role'] == 'student':
            # Get student's recent learning activities
            recent_activities = connection.execute("""
                SELECT c.id as content_id, c.title, c.type, ua.activity_type, ua.created_at 
                FROM user_activities ua 
                JOIN content c ON ua.content_id = c.id 
                WHERE ua.user_id = ? 
                ORDER BY ua.created_at DESC 
                LIMIT 5
            """, (session['user_id'],)).fetchall()
        elif user and user['role'] == 'instructor':
            # Get instructor's uploaded content
            recent_activities = connection.execute("""
                SELECT id as content_id, title, type, created_at 
                FROM content 
                WHERE uploaded_by = ? 
                ORDER BY created_at DESC 
                LIMIT 5
            """, (session['user_id'],)).fetchall()
        else:
            recent_activities = []
        
        # Get recommended content for students
        recommended_content = []
        user_stats = {}
        if user and user['role'] == 'student':
            recommended_content = connection.execute("""
                SELECT c.*, cat.name as category_name
                FROM content c 
                LEFT JOIN categories cat ON c.category_id = cat.id
                WHERE c.is_published = 1 
                ORDER BY c.average_rating DESC, c.view_count DESC 
                LIMIT 3
            """).fetchall()
            
            # Calculate user statistics
            # 1. Learning Progress - percentage of completed content
            total_content = connection.execute("""
                SELECT COUNT(*) as count FROM content WHERE is_published = 1
            """).fetchone()['count']
            
            completed_content = connection.execute("""
                SELECT COUNT(DISTINCT ua.content_id) as count 
                FROM user_activities ua 
                WHERE ua.user_id = ? AND ua.activity_type = 'completed'
            """, (session['user_id'],)).fetchone()['count']
            
            learning_progress = round((completed_content / total_content * 100), 1) if total_content > 0 else 0
            
            # 2. Completed - number of completed activities
            completed_count = connection.execute("""
                SELECT COUNT(*) as count 
                FROM user_activities ua 
                WHERE ua.user_id = ? AND ua.activity_type = 'completed'
            """, (session['user_id'],)).fetchone()['count']
            
            # 3. In Progress - content accessed but not completed
            in_progress_count = connection.execute("""
                SELECT COUNT(DISTINCT ua.content_id) as count 
                FROM user_activities ua 
                WHERE ua.user_id = ? AND ua.activity_type != 'completed'
            """, (session['user_id'],)).fetchone()['count']
            
            # 4. Achievements - count of positive ratings given or milestones
            achievements_count = connection.execute("""
                SELECT COUNT(*) as count 
                FROM content_feedback cf 
                WHERE cf.user_id = ? AND cf.rating >= 4
            """, (session['user_id'],)).fetchone()['count']
            
            user_stats = {
                'learning_progress': learning_progress,
                'completed_count': completed_count,
                'in_progress_count': in_progress_count,
                'achievements_count': achievements_count
            }
        
        return render_template('dashboard.html', 
                             user=user, 
                             recent_activities=recent_activities,
                             recommended_content=recommended_content,
                             user_stats=user_stats)
    
    except Exception as e:
        flash('Error loading dashboard', 'error')
        return render_template('dashboard.html', user=None, recent_activities=[])
    finally:
        if connection:
            connection.close()

@app.errorhandler(404)
def not_found(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f'Internal Server Error: {error}')
    return render_template('errors/500.html'), 500

if __name__ == '__main__':
    app.run(
        debug=app.config.get('DEBUG', True),
        host=app.config.get('HOST', '0.0.0.0'),
        port=app.config.get('PORT', 5000)
    )