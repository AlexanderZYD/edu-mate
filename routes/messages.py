"""
Messages Route - Internal Messaging System
Handles private messages between users and system notifications
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
import sqlite3
from datetime import datetime
from functools import wraps

# Create blueprint
messages_bp = Blueprint('messages', __name__, url_prefix='/messages')

# Decorator for login required
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def get_db_connection():
    """Get database connection"""
    try:
        conn = sqlite3.connect('edumate_local.db', timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys = ON')
        return conn
    except sqlite3.Error as err:
        print(f"Database error: {err}")
        return None

def get_unread_count(user_id):
    """Get unread message count for user"""
    connection = get_db_connection()
    if not connection:
        return 0
    
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM messages 
            WHERE receiver_id = ? AND is_read = FALSE AND is_deleted_by_receiver = FALSE
        """, (user_id,))
        result = cursor.fetchone()
        return result['count'] if result else 0
    except Exception as err:
        print(f"Error getting unread count: {err}")
        return 0
    finally:
        connection.close()

@messages_bp.route('/api/unread-count')
@login_required
def api_unread_count():
    """API endpoint to get unread message count"""
    count = get_unread_count(session['user_id'])
    return jsonify({'count': count})

@messages_bp.route('/')
@login_required
def inbox():
    """Display user's inbox"""
    connection = get_db_connection()
    if not connection:
        flash('Database connection error.', 'error')
        return render_template('messages/inbox.html', messages=[])
    
    try:
        cursor = connection.cursor()
        
        # Get received messages
        cursor.execute("""
            SELECT m.*, u_sender.full_name as sender_name, u_sender.email as sender_email,
                   c.title as content_title
            FROM messages m
            LEFT JOIN users u_sender ON m.sender_id = u_sender.id
            LEFT JOIN content c ON m.related_content_id = c.id
            WHERE m.receiver_id = ? AND m.is_deleted_by_receiver = FALSE
            ORDER BY m.sent_at DESC
        """, (session['user_id'],))
        received_messages = cursor.fetchall()
        
        # Get sent messages
        cursor.execute("""
            SELECT m.*, u_receiver.full_name as receiver_name, u_receiver.email as receiver_email,
                   c.title as content_title
            FROM messages m
            LEFT JOIN users u_receiver ON m.receiver_id = u_receiver.id
            LEFT JOIN content c ON m.related_content_id = c.id
            WHERE m.sender_id = ? AND m.is_deleted_by_sender = FALSE
            ORDER BY m.sent_at DESC
        """, (session['user_id'],))
        sent_messages = cursor.fetchall()
        
        return render_template('messages/inbox.html', 
                             received_messages=received_messages,
                             sent_messages=sent_messages,
                             unread_count=get_unread_count(session['user_id']))
    
    except Exception as err:
        flash(f'Error loading messages: {err}', 'error')
        return render_template('messages/inbox.html', received_messages=[], sent_messages=[])
    
    finally:
        connection.close()

@messages_bp.route('/<int:message_id>')
@login_required
def view_message(message_id):
    """View a specific message"""
    connection = get_db_connection()
    if not connection:
        flash('Database connection error.', 'error')
        return redirect(url_for('messages.inbox'))
    
    try:
        cursor = connection.cursor()
        
        # Get message with related info
        cursor.execute("""
            SELECT m.*, u_sender.full_name as sender_name, u_sender.email as sender_email,
                   u_receiver.full_name as receiver_name, u_receiver.email as receiver_email,
                   c.title as content_title
            FROM messages m
            LEFT JOIN users u_sender ON m.sender_id = u_sender.id
            LEFT JOIN users u_receiver ON m.receiver_id = u_receiver.id
            LEFT JOIN content c ON m.related_content_id = c.id
            WHERE m.id = ? AND (
                (m.receiver_id = ? AND m.is_deleted_by_receiver = FALSE) OR
                (m.sender_id = ? AND m.is_deleted_by_sender = FALSE)
            )
        """, (message_id, session['user_id'], session['user_id']))
        message = cursor.fetchone()
        
        if not message:
            flash('Message not found or access denied.', 'error')
            return redirect(url_for('messages.inbox'))
        
        # Mark as read if user is receiver
        if message['receiver_id'] == session['user_id'] and not message['is_read']:
            cursor.execute("""
                UPDATE messages 
                SET is_read = TRUE, read_at = ?
                WHERE id = ?
            """, (datetime.now(), message_id))
            connection.commit()
        
        return render_template('messages/view.html', message=message)
    
    except Exception as err:
        if 'connection' in locals() and connection:
            connection.close()
        flash(f'Error viewing message: {err}', 'error')
        return redirect(url_for('messages.inbox'))
    
    if 'connection' in locals() and connection:
        connection.close()

@messages_bp.route('/compose', methods=['GET', 'POST'])
@login_required
def compose_message():
    """Compose a new message"""
    if request.method == 'GET':
        # Get list of users to send message to
        connection = get_db_connection()
        users = []
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute("""
                    SELECT id, full_name, email, role
                    FROM users
                    WHERE id != ? AND is_active = TRUE
                    ORDER BY full_name
                """, (session['user_id'],))
                users = cursor.fetchall()
            except Exception as err:
                flash(f'Error loading users: {err}', 'error')
            finally:
                connection.close()
        
        return render_template('messages/compose.html', users=users)
    
    # POST request - send message
    receiver_id = request.form.get('receiver_id')
    subject = request.form.get('subject', '').strip()
    content = request.form.get('content', '').strip()
    
    # Validation
    if not receiver_id or not subject or not content:
        flash('All fields are required.', 'error')
        return redirect(url_for('messages.compose_message'))
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error.', 'error')
        return redirect(url_for('messages.compose_message'))
    
    try:
        cursor = connection.cursor()
        
        # Insert message
        cursor.execute("""
            INSERT INTO messages 
            (sender_id, receiver_id, subject, content, message_type, sent_at)
            VALUES (?, ?, ?, ?, 'personal', ?)
        """, (session['user_id'], receiver_id, subject, content, datetime.now()))
        
        connection.commit()
        flash('Message sent successfully!', 'success')
        return redirect(url_for('messages.inbox'))
    
    except Exception as err:
        connection.rollback()
        flash(f'Error sending message: {err}', 'error')
        return redirect(url_for('messages.compose_message'))
    
    finally:
        connection.close()

@messages_bp.route('/reply/<int:message_id>', methods=['GET', 'POST'])
@login_required
def reply_message(message_id):
    """Reply to a message"""
    connection = get_db_connection()
    if not connection:
        flash('Database connection error.', 'error')
        return redirect(url_for('messages.inbox'))
    
    try:
        cursor = connection.cursor()
        
        # Get original message
        cursor.execute("""
            SELECT m.*, u_sender.full_name as sender_name, u_sender.email as sender_email
            FROM messages m
            LEFT JOIN users u_sender ON m.sender_id = u_sender.id
            WHERE m.id = ? AND m.receiver_id = ? AND m.is_deleted_by_receiver = FALSE
        """, (message_id, session['user_id']))
        original_message = cursor.fetchone()
        
        if not original_message:
            flash('Message not found or access denied.', 'error')
            return redirect(url_for('messages.inbox'))
        
        if request.method == 'GET':
            return render_template('messages/reply.html', 
                                 original_message=original_message)
        
        # POST request - send reply
        content = request.form.get('content', '').strip()
        
        if not content:
            flash('Message content is required.', 'error')
            return render_template('messages/reply.html', 
                                 original_message=original_message)
        
        # Insert reply
        cursor.execute("""
            INSERT INTO messages 
            (sender_id, receiver_id, subject, content, message_type, parent_message_id, sent_at)
            VALUES (?, ?, ?, ?, 'personal', ?, ?)
        """, (session['user_id'], original_message['sender_id'], 
              f"Re: {original_message['subject']}", content, 
              message_id, datetime.now()))
        
        connection.commit()
        flash('Reply sent successfully!', 'success')
        return redirect(url_for('messages.inbox'))
    
    except Exception as err:
        connection.rollback()
        flash(f'Error sending reply: {err}', 'error')
        return render_template('messages/reply.html', 
                             original_message=original_message)
    
    finally:
        connection.close()

@messages_bp.route('/mark-read/<int:message_id>', methods=['POST'])
@login_required
def mark_as_read(message_id):
    """Mark message as read (AJAX endpoint)"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'success': False, 'error': 'Database connection error'})
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            UPDATE messages 
            SET is_read = TRUE, read_at = ?
            WHERE id = ? AND receiver_id = ?
        """, (datetime.now(), message_id, session['user_id']))
        
        connection.commit()
        
        unread_count = get_unread_count(session['user_id'])
        return jsonify({'success': True, 'unread_count': unread_count})
    
    except Exception as err:
        connection.rollback()
        return jsonify({'success': False, 'error': str(err)})
    
    finally:
        connection.close()

@messages_bp.route('/delete/<int:message_id>', methods=['POST'])
@login_required
def delete_message(message_id):
    """Delete message for current user"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'success': False, 'error': 'Database connection error'})
    
    try:
        cursor = connection.cursor()
        
        # Check message ownership
        cursor.execute("""
            SELECT sender_id, receiver_id 
            FROM messages 
            WHERE id = ?
        """, (message_id,))
        message = cursor.fetchone()
        
        if not message:
            return jsonify({'success': False, 'error': 'Message not found'})
        
        # Mark as deleted for appropriate user
        if message['sender_id'] == session['user_id']:
            cursor.execute("""
                UPDATE messages 
                SET is_deleted_by_sender = TRUE 
                WHERE id = ?
            """, (message_id,))
        elif message['receiver_id'] == session['user_id']:
            cursor.execute("""
                UPDATE messages 
                SET is_deleted_by_receiver = TRUE 
                WHERE id = ?
            """, (message_id,))
        else:
            return jsonify({'success': False, 'error': 'Access denied'})
        
        connection.commit()
        return jsonify({'success': True})
    
    except Exception as err:
        connection.rollback()
        return jsonify({'success': False, 'error': str(err)})
    
    finally:
        connection.close()

@messages_bp.route('/notifications')
@login_required
def notification_settings():
    """Display and manage notification settings"""
    connection = get_db_connection()
    if not connection:
        flash('Database connection error.', 'error')
        return render_template('messages/notifications.html', notifications=[])
    
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT * 
            FROM message_notifications 
            WHERE user_id = ?
        """, (session['user_id'],))
        notifications = cursor.fetchall()
        
        return render_template('messages/notifications.html', notifications=notifications)
    
    except Exception as err:
        flash(f'Error loading notification settings: {err}', 'error')
        return render_template('messages/notifications.html', notifications=[])
    
    finally:
        connection.close()

@messages_bp.route('/check-publication-request/<int:content_id>', methods=['GET'])
@login_required
def check_publication_request(content_id):
    """Check if a publication request already exists for this content"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'exists': False, 'error': 'Database connection error'})
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM messages
            WHERE sender_id = ? 
              AND receiver_id = 1
              AND related_content_id = ?
              AND subject LIKE ?
              AND is_deleted_by_sender = FALSE
              AND is_deleted_by_receiver = FALSE
        """, (session['user_id'], content_id, '%Publication Request%'))
        
        result = cursor.fetchone()
        exists = result['count'] > 0
        
        return jsonify({'exists': exists})
    
    except Exception as err:
        return jsonify({'exists': False, 'error': str(err)})
    
    finally:
        connection.close()

@messages_bp.route('/send', methods=['POST'])
@login_required
def send_message():
    """Send a message (AJAX endpoint)"""
    try:
        data = request.get_json()
        receiver_id = data.get('receiver_id')
        subject = data.get('subject', '').strip()
        content = data.get('content', '').strip()
        related_content_id = data.get('related_content_id')
        
        # Validation
        if not receiver_id or not subject or not content:
            return jsonify({'success': False, 'error': 'All fields are required'}), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'error': 'Database connection error'})
        
        cursor = connection.cursor()
        
        # Check if this is a publication request and if one already exists for this content
        if 'Publication Request' in subject and related_content_id:
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM messages
                WHERE sender_id = ? 
                  AND receiver_id = ? 
                  AND related_content_id = ?
                  AND subject LIKE ?
                  AND is_deleted_by_sender = FALSE
                  AND is_deleted_by_receiver = FALSE
            """, (session['user_id'], receiver_id, related_content_id, f'%Publication Request%'))
            
            existing_request = cursor.fetchone()
            if existing_request and existing_request['count'] > 0:
                connection.close()
                return jsonify({
                    'success': False, 
                    'error': 'You have already sent a publication request for this content. Please wait for admin review.'
                }), 400
        
        # Insert message
        cursor.execute("""
            INSERT INTO messages 
            (sender_id, receiver_id, subject, content, message_type, related_content_id, sent_at)
            VALUES (?, ?, ?, ?, 'personal', ?, ?)
        """, (session['user_id'], receiver_id, subject, content, related_content_id, datetime.now()))
        
        connection.commit()
        connection.close()
        
        return jsonify({'success': True, 'message': 'Message sent successfully'})
    
    except Exception as err:
        return jsonify({'success': False, 'error': str(err)}), 500

@messages_bp.route('/notifications', methods=['POST'])
@login_required
def update_notification_settings():
    """Update notification settings"""
    connection = get_db_connection()
    if not connection:
        flash('Database connection error.', 'error')
        return redirect(url_for('messages.notification_settings'))
    
    try:
        cursor = connection.cursor()
        
        # Update each notification type
        for notification_type in ['new_message', 'message_reply', 'system_announcement', 'content_feedback']:
            is_enabled = request.form.get(f'{notification_type}_enabled') == 'on'
            email_enabled = request.form.get(f'{notification_type}_email') == 'on'
            
            cursor.execute("""
                UPDATE message_notifications 
                SET is_enabled = ?, email_enabled = ?, updated_at = ?
                WHERE user_id = ? AND notification_type = ?
            """, (is_enabled, email_enabled, datetime.now(), 
                  session['user_id'], notification_type))
        
        connection.commit()
        flash('Notification settings updated successfully!', 'success')
        return redirect(url_for('messages.notification_settings'))
    
    except Exception as err:
        connection.rollback()
        flash(f'Error updating settings: {err}', 'error')
        return redirect(url_for('messages.notification_settings'))
    
    finally:
        connection.close()

# Helper function to send system messages
def send_system_message(receiver_id, subject, content, message_type='system', 
                       related_content_id=None, related_user_id=None):
    """Send a system message to a user"""
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        # Use admin user (ID=1) as sender for system messages
        cursor.execute("""
            INSERT INTO messages 
            (sender_id, receiver_id, subject, content, message_type, 
             related_content_id, related_user_id, sent_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (1, receiver_id, subject, content, message_type, 
              related_content_id, related_user_id, datetime.now()))
        
        connection.commit()
        return True
    
    except Exception as err:
        print(f"Error sending system message: {err}")
        connection.rollback()
        return False
    
    finally:
        connection.close()