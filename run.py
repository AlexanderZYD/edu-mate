"""
EduMate Application Runner
"""
from app import app
import os

if __name__ == '__main__':
    # Run the Flask application
    app.run(
        debug=app.config.get('DEBUG', True),
        host=app.config.get('HOST', '0.0.0.0'),
        port=app.config.get('PORT', 5000)
    )