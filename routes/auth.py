"""
Authentication Routes - Login, Register, Logout
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

auth_bp = Blueprint('auth', __name__)

def get_db_connection():
    """Get database connection"""
    try:
        conn = sqlite3.connect('edumate_local.db')
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        current_app.logger.debug("Database connection established successfully")
        return conn
    except Exception as err:
        current_app.logger.error(f"Database connection error: {err}")
        flash(f'Database error: {err}', 'error')
        return None

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if 'user_id' in session:
        # Redirect based on user role
        if session.get('user_role') == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif session.get('user_role') == 'instructor':
            return redirect(url_for('user.profile'))
        else:  # student
            return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Please enter both email and password', 'error')
            return render_template('auth/login.html')
        
        connection = get_db_connection()
        if not connection:
            return render_template('auth/login.html')
        
        try:
            user = connection.execute(
                "SELECT * FROM users WHERE email = ? AND is_active = 1",
                (email,)
            ).fetchone()
            
            if user and check_password_hash(user['password_hash'], password):
                # Successful login
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['email'] = user['email']
                session['full_name'] = user['full_name']
                session['role'] = user['role']
                session['user_role'] = user['role']  # Add user_role for template compatibility
                
                # Update last login
                connection.execute(
                    "UPDATE users SET last_login = ? WHERE id = ?",
                    (datetime.now(), user['id'])
                )
                connection.commit()
                
                flash(f'Welcome back, {user["full_name"]}!', 'success')
                
                # Redirect based on user role
                if user['role'] == 'admin':
                    return redirect(url_for('admin.dashboard'))
                elif user['role'] == 'instructor':
                    return redirect(url_for('user.profile'))
                else:  # student
                    return redirect(url_for('index'))
            else:
                flash('Invalid email or password', 'error')
                
        except Exception as err:
            flash(f'Login error: {err}', 'error')
        finally:
            if connection:
                connection.close()
    
    return render_template('auth/login.html')

@auth_bp.route('/register-nojs', methods=['GET', 'POST'])
def register_nojs():
    """Handle user registration without JavaScript"""
    if 'user_id' in session:
        # Redirect based on user role
        if session.get('user_role') == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif session.get('user_role') == 'instructor':
            return redirect(url_for('user.profile'))
        else:  # student
            return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        full_name = request.form.get('full_name')
        id_number = request.form.get('id_number', '').strip()
        role = request.form.get('role', 'student')
        interests = request.form.getlist('interests')
        terms = request.form.get('terms')
        
        # Validation
        if not all([username, email, password, full_name, id_number]):
            flash('Please fill in all required fields', 'error')
            return render_template('auth/register_nojs.html')
        
        # Validate ID number - must be digits only
        if not id_number.isdigit():
            flash('ID number must contain numbers only', 'error')
            return render_template('auth/register_nojs.html')
        
        # Validate email - must be in format @____.com
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.com$'
        if not re.match(email_pattern, email):
            flash('Email must be in format username@domain.com', 'error')
            return render_template('auth/register_nojs.html')
        
        # Validate password - only letters (a-z, A-Z) and numbers allowed
        password_pattern = r'^[a-zA-Z0-9]+$'
        if not re.match(password_pattern, password):
            flash('Password can only contain letters (a-z, A-Z) and numbers, no special symbols', 'error')
            return render_template('auth/register_nojs.html')
        
        if not terms:
            flash('You must agree to the terms and conditions', 'error')
            return render_template('auth/register_nojs.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('auth/register_nojs.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return render_template('auth/register_nojs.html')
        
        connection = get_db_connection()
        if not connection:
            return render_template('auth/register_nojs.html')
        
        try:
            # Check if username, email, or ID number already exists
            existing_user = connection.execute(
                "SELECT id FROM users WHERE username = ? OR email = ? OR id_number = ?",
                (username, email, id_number)
            ).fetchone()
            
            if existing_user:
                flash('Username, email, or ID number already exists', 'error')
                return render_template('auth/register_nojs.html')
            
            # Insert new user
            password_hash = generate_password_hash(password)
            interests_json = str(interests) if interests else None
            
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO users 
                (username, email, password_hash, full_name, id_number, role, interests, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                username, email, password_hash, full_name, id_number, role,
                interests_json, datetime.now(), datetime.now()
            ))
            
            user_id = cursor.lastrowid
            
            # Create user preferences entry
            cursor.execute("""
                INSERT INTO user_preferences (user_id, created_at, updated_at)
                VALUES (?, ?, ?)
            """, (user_id, datetime.now(), datetime.now()))
            
            connection.commit()
            
            # Log the registration
            cursor.execute("""
                INSERT INTO system_logs (user_id, action, resource_type, created_at)
                VALUES (?, ?, ?, ?)
            """, (user_id, 'REGISTERED', 'user', datetime.now()))
            connection.commit()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as err:
            flash(f'Registration error: {err}', 'error')
        finally:
            if 'cursor' in locals():
                cursor.close()
            if connection:
                connection.close()
    
    return render_template('auth/register_nojs.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration"""
    if 'user_id' in session:
        # Redirect based on user role
        if session.get('user_role') == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif session.get('user_role') == 'instructor':
            return redirect(url_for('user.profile'))
        else:  # student
            return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        full_name = request.form.get('full_name')
        id_number = request.form.get('id_number', '').strip()
        role = request.form.get('role', 'student')
        interests = request.form.getlist('interests')
        terms = request.form.get('terms')
        
        # Validation
        if not all([username, email, password, full_name, id_number]):
            flash('Please fill in all required fields', 'error')
            return render_template('auth/register.html')
        
        # Validate ID number - must be digits only
        if not id_number.isdigit():
            flash('ID number must contain numbers only', 'error')
            return render_template('auth/register.html')
        
        # Validate email - must be in format @____.com
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.com$'
        if not re.match(email_pattern, email):
            flash('Email must be in format username@domain.com', 'error')
            return render_template('auth/register.html')
        
        # Validate password - only letters (a-z, A-Z) and numbers allowed
        password_pattern = r'^[a-zA-Z0-9]+$'
        if not re.match(password_pattern, password):
            flash('Password can only contain letters (a-z, A-Z) and numbers, no special symbols', 'error')
            return render_template('auth/register.html')
        
        if not terms:
            flash('You must agree to the terms and conditions', 'error')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('auth/register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return render_template('auth/register.html')
        
        connection = get_db_connection()
        if not connection:
            return render_template('auth/register.html')
        
        try:
            # Check if username, email, or ID number already exists
            existing_user = connection.execute(
                "SELECT id FROM users WHERE username = ? OR email = ? OR id_number = ?",
                (username, email, id_number)
            ).fetchone()
            
            if existing_user:
                flash('Username, email, or ID number already exists', 'error')
                return render_template('auth/register.html')
            
            # Insert new user
            password_hash = generate_password_hash(password)
            interests_json = str(interests) if interests else None
            
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO users 
                (username, email, password_hash, full_name, id_number, role, interests, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                username, email, password_hash, full_name, id_number, role,
                interests_json, datetime.now(), datetime.now()
            ))
            
            user_id = cursor.lastrowid
            
            # Create user preferences entry
            cursor.execute("""
                INSERT INTO user_preferences (user_id, created_at, updated_at)
                VALUES (?, ?, ?)
            """, (user_id, datetime.now(), datetime.now()))
            
            connection.commit()
            
            # Log the registration
            cursor.execute("""
                INSERT INTO system_logs (user_id, action, resource_type, created_at)
                VALUES (?, ?, ?, ?)
            """, (user_id, 'REGISTERED', 'user', datetime.now()))
            connection.commit()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as err:
            flash(f'Registration error: {err}', 'error')
        finally:
            if 'cursor' in locals():
                cursor.close()
            if connection:
                connection.close()
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    """Handle user logout"""
    if 'user_id' in session:
        # Log the logout
        connection = get_db_connection()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute("""
                    INSERT INTO system_logs (user_id, action, resource_type, created_at)
                    VALUES (?, ?, ?, ?)
                """, (session['user_id'], 'LOGOUT', 'user', datetime.now()))
                connection.commit()
                cursor.close()
            except:
                pass
            connection.close()
        
        # Clear session
        session.clear()
        
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Handle password recovery using email and ID number"""
    if 'user_id' in session:
        # Redirect based on user role
        if session.get('user_role') == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif session.get('user_role') == 'instructor':
            return redirect(url_for('user.profile'))
        else:  # student
            return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        id_number = request.form.get('id_number', '').strip()
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        # Validation
        if not email or not id_number:
            flash('Please provide both email and ID number', 'error')
            return render_template('auth/forgot_password.html')
        
        if not new_password or not confirm_password:
            flash('Please provide and confirm your new password', 'error')
            return render_template('auth/forgot_password.html')
        
        # Validate passwords
        if new_password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('auth/forgot_password.html')
        
        if len(new_password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return render_template('auth/forgot_password.html')
        
        # Update password
        connection = get_db_connection()
        if not connection:
            flash('Database error. Please try again later.', 'error')
            return render_template('auth/forgot_password.html')
        
        try:
            # Debug: Log the search attempt
            current_app.logger.debug(f"Debug: Searching for email='{email}', id_number='{id_number}'")
            
            # First, let's see if user exists with this email
            email_user = connection.execute(
                "SELECT id, id_number, is_active FROM users WHERE email = ?",
                (email,)
            ).fetchone()
            
            if email_user:
                current_app.logger.debug(f"Debug: Found user by email: {dict(email_user)}")
                current_app.logger.debug(f"Debug: User ID: {email_user['id']}, Stored ID Number: {email_user['id_number']}, Active: {email_user['is_active']}")
            else:
                current_app.logger.debug(f"Debug: No user found with email: {email}")
            
            # Find user and update password
            user = connection.execute(
                "SELECT id FROM users WHERE email = ? AND id_number = ? AND is_active = 1",
                (email, id_number)
            ).fetchone()
            
            if user:
                current_app.logger.debug(f"Debug: User found successfully, updating password...")
                # Update password
                password_hash = generate_password_hash(new_password)
                cursor = connection.cursor()
                cursor.execute(
                    "UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?",
                    (password_hash, datetime.now(), user['id'])
                )
                
                # Log the password reset
                cursor.execute("""
                    INSERT INTO system_logs (user_id, action, resource_type, created_at)
                    VALUES (?, ?, ?, ?)
                """, (user['id'], 'PASSWORD_RESET', 'user', datetime.now()))
                
                connection.commit()
                cursor.close()
                
                flash('Password reset successfully! Please login with your new password.', 'success')
                return redirect(url_for('auth.login'))
            else:
                flash(f'Invalid email or ID number combination. Email: {email}, ID: {id_number}', 'error')
                
        except Exception as err:
            flash(f'Error resetting password: {err}', 'error')
            current_app.logger.error(f"Debug: Exception occurred: {err}")
            import traceback
            current_app.logger.error(f"Debug: Traceback: {traceback.format_exc()}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if connection:
                connection.close()
    
    # GET request or form validation failed
    return render_template('auth/forgot_password.html')



