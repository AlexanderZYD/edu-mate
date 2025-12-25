// EduMate Main JavaScript File
// Common functionality for the EduMate platform

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize form validations
    initializeFormValidations();
    
    // Initialize auto-hide alerts
    initializeAutoHideAlerts();
    
    // Initialize loading states
    initializeLoadingStates();
    
    // Initialize smooth scrolling
    initializeSmoothScrolling();
});

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize form validations
 */
function initializeFormValidations() {
    // Bootstrap form validation
    var forms = document.querySelectorAll('.needs-validation');
    
    Array.prototype.slice.call(forms).forEach(function (form) {
        form.addEventListener('submit', function (event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
    
    // Custom validation for specific fields
    // Skip if there's a change password form (it has its own validation)
    const changePasswordForm = document.getElementById('changePasswordForm');
    if (!changePasswordForm) {
        const passwordField = document.querySelector('input[type="password"]');
        const confirmPasswordField = document.querySelector('input[name="confirm_password"]');
        
        // Only apply this validation if it's a registration form or simple password form
        // Skip for change password forms which have their own validation logic
        if (passwordField && confirmPasswordField && 
            passwordField.id !== 'current_password' && 
            passwordField.id !== 'new_password') {
            confirmPasswordField.addEventListener('input', function() {
                if (this.value !== passwordField.value) {
                    this.setCustomValidity('Passwords do not match');
                } else {
                    this.setCustomValidity('');
                }
            });
        }
    }
}

/**
 * Initialize auto-hide alerts
 */
function initializeAutoHideAlerts() {
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000); // Auto-hide after 5 seconds
    });
}

/**
 * Initialize loading states for buttons
 */
function initializeLoadingStates() {
    const buttonsWithLoading = document.querySelectorAll('[data-loading-text]');
    
    buttonsWithLoading.forEach(function(button) {
        button.addEventListener('click', function(e) {
            // Don't interfere with form submit buttons
            if (button.type === 'submit' || button.form) {
                return; // Let the form handle the submission
            }
            
            const originalText = button.innerHTML;
            const loadingText = button.getAttribute('data-loading-text') || 'Loading...';
            
            button.disabled = true;
            button.innerHTML = `<span class="spinner"></span> ${loadingText}`;
            
            // Reset after 10 seconds (fallback)
            setTimeout(function() {
                button.disabled = false;
                button.innerHTML = originalText;
            }, 10000);
        });
    });
}

/**
 * Initialize smooth scrolling for anchor links
 */
function initializeSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

/**
 * AJAX helper function
 */
function ajaxRequest(url, options = {}) {
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    };
    
    const finalOptions = { ...defaultOptions, ...options };
    
    return fetch(url, finalOptions)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .catch(error => {
            console.error('AJAX Error:', error);
            showNotification('An error occurred. Please try again.', 'danger');
            throw error;
        });
}

/**
 * Show notification message
 */
function showNotification(message, type = 'info') {
    // Create or get notification container
    let notificationContainer = document.getElementById('notification-container');
    if (!notificationContainer) {
        notificationContainer = document.createElement('div');
        notificationContainer.id = 'notification-container';
        notificationContainer.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            max-width: 400px;
        `;
        document.body.appendChild(notificationContainer);
    }
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show mb-2`;
    alertDiv.style.cssText = `
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        border-radius: 8px;
        animation: slideInRight 0.3s ease-out;
    `;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    notificationContainer.appendChild(alertDiv);
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        alertDiv.style.animation = 'slideOutRight 0.3s ease-in';
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.parentNode.removeChild(alertDiv);
            }
        }, 300);
    }, 5000);
}

/**
 * Format date to human readable format
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    const options = { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    return date.toLocaleDateString('en-US', options);
}

/**
 * Format file size
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Rate content functionality
 */
function rateContent(contentId, rating, comment = '') {
    return ajaxRequest(`/api/content/${contentId}/rate`, {
        method: 'POST',
        body: JSON.stringify({
            rating: rating,
            comment: comment
        })
    })
    .then(data => {
        showNotification('Thank you for your feedback!', 'success');
        updateRatingDisplay(contentId, data.new_average, data.new_count);
    });
}

/**
 * Update rating display
 */
function updateRatingDisplay(contentId, average, count) {
    const ratingContainer = document.querySelector(`#rating-${contentId}`);
    if (ratingContainer) {
        ratingContainer.innerHTML = `
            <div class="rating">
                ${generateStars(average)} ${average.toFixed(1)} (${count} reviews)
            </div>
        `;
    }
}

/**
 * Generate star rating HTML
 */
function generateStars(rating) {
    let stars = '';
    for (let i = 1; i <= 5; i++) {
        if (i <= Math.floor(rating)) {
            stars += '<i class="fas fa-star"></i>';
        } else if (i - 0.5 <= rating) {
            stars += '<i class="fas fa-star-half-alt"></i>';
        } else {
            stars += '<i class="far fa-star empty"></i>';
        }
    }
    return stars;
}

/**
 * Search content with debounce
 */
let searchTimeout;
function searchContent(query) {
    clearTimeout(searchTimeout);
    
    searchTimeout = setTimeout(() => {
        if (query.length < 2) {
            clearSearchResults();
            return;
        }
        
        ajaxRequest(`/api/search?q=${encodeURIComponent(query)}`)
            .then(data => {
                displaySearchResults(data.results);
            });
    }, 300);
}

/**
 * Display search results
 */
function displaySearchResults(results) {
    const resultsContainer = document.getElementById('search-results');
    if (!resultsContainer) return;
    
    if (results.length === 0) {
        resultsContainer.innerHTML = '<div class="text-muted">No results found</div>';
        return;
    }
    
    let html = '';
    results.forEach(result => {
        html += `
            <div class="search-result-item p-3 border-bottom">
                <h6><a href="/content/${result.id}">${result.title}</a></h6>
                <p class="text-muted small mb-1">${result.description}</p>
                <small class="text-muted">${result.type} • ${result.category}</small>
            </div>
        `;
    });
    
    resultsContainer.innerHTML = html;
}

/**
 * Clear search results
 */
function clearSearchResults() {
    const resultsContainer = document.getElementById('search-results');
    if (resultsContainer) {
        resultsContainer.innerHTML = '';
    }
}

/**
 * Bookmark content
 */
function toggleBookmark(contentId, button) {
    const isBookmarked = button.classList.contains('bookmarked');
    
    ajaxRequest(`/api/content/${contentId}/bookmark`, {
        method: isBookmarked ? 'DELETE' : 'POST'
    })
    .then(data => {
        button.classList.toggle('bookmarked');
        button.innerHTML = isBookmarked ? 
            '<i class="far fa-bookmark"></i> Bookmark' : 
            '<i class="fas fa-bookmark"></i> Bookmarked';
        
        showNotification(
            isBookmarked ? 'Bookmark removed' : 'Content bookmarked',
            'success'
        );
    });
}

/**
 * Initialize rating interactions
 */
document.querySelectorAll('.rating-input').forEach(ratingInput => {
    const stars = ratingInput.querySelectorAll('.star');
    const contentId = ratingInput.dataset.contentId;
    
    stars.forEach((star, index) => {
        star.addEventListener('click', () => {
            const rating = index + 1;
            rateContent(contentId, rating);
            
            // Update visual feedback
            stars.forEach((s, i) => {
                s.classList.toggle('text-warning', i < rating);
                s.classList.toggle('text-muted', i >= rating);
            });
        });
        
        star.addEventListener('mouseenter', () => {
            stars.forEach((s, i) => {
                s.classList.toggle('text-warning', i <= index);
                s.classList.toggle('text-muted', i > index);
            });
        });
    });
    
    ratingInput.addEventListener('mouseleave', () => {
        const currentRating = parseInt(ratingInput.dataset.currentRating) || 0;
        stars.forEach((s, i) => {
            s.classList.toggle('text-warning', i < currentRating);
            s.classList.toggle('text-muted', i >= currentRating);
        });
    });
});

/**
 * Message system functions
 */

/**
 * Periodically check for new messages and update unread count
 */
function startMessagePolling() {
    // Only poll if user is logged in
    if (document.querySelector('a[href*="/messages"]')) {
        setInterval(updateUnreadCount, 30000); // Check every 30 seconds
    }
}

/**
 * Update unread message count in navigation
 */
function updateUnreadCount() {
    fetch('/messages/api/unread-count', {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        const unreadBadge = document.getElementById('unread-count');
        if (unreadBadge) {
            if (data.count > 0) {
                unreadBadge.textContent = data.count;
                unreadBadge.style.display = 'block';
            } else {
                unreadBadge.style.display = 'none';
            }
        }
    })
    .catch(error => {
        // Silently fail - not critical
        console.log('Failed to update unread count:', error);
    });
}

/**
 * Send message with real-time feedback
 */
function sendMessage(formData) {
    return ajaxRequest('/messages/send', {
        method: 'POST',
        body: formData
    })
    .then(data => {
        if (data.success) {
            showNotification('Message sent successfully!', 'success');
            return data;
        } else {
            throw new Error(data.error || 'Failed to send message');
        }
    });
}

/**
 * Mark message as read with animation
 */
function markMessageAsRead(messageId) {
    return ajaxRequest(`/messages/mark-read/${messageId}`, {
        method: 'POST'
    })
    .then(data => {
        if (data.success) {
            // Update UI with animation
            const messageElement = document.querySelector(`[data-message-id="${messageId}"]`);
            if (messageElement) {
                messageElement.classList.add('fade');
                setTimeout(() => {
                    messageElement.classList.remove('unread');
                    messageElement.classList.remove('fade');
                }, 300);
            }
            
            // Update unread count
            updateUnreadCount();
            
            return data;
        } else {
            throw new Error(data.error || 'Failed to mark message as read');
        }
    });
}

/**
 * Delete message with confirmation
 */
function deleteMessage(messageId) {
    if (!confirm('Are you sure you want to delete this message?')) {
        return Promise.reject(new Error('User cancelled deletion'));
    }
    
    return ajaxRequest(`/messages/delete/${messageId}`, {
        method: 'POST'
    })
    .then(data => {
        if (data.success) {
            // Animate removal
            const messageElement = document.querySelector(`[data-message-id="${messageId}"]`);
            if (messageElement) {
                messageElement.style.transition = 'opacity 0.3s, transform 0.3s';
                messageElement.style.opacity = '0';
                messageElement.style.transform = 'translateX(-20px)';
                
                setTimeout(() => {
                    messageElement.remove();
                    showNotification('Message deleted successfully', 'success');
                }, 300);
            }
            
            return data;
        } else {
            throw new Error(data.error || 'Failed to delete message');
        }
    });
}

/**
 * Initialize message-related functionality
 */
function initializeMessageSystem() {
    // Start polling for new messages
    startMessagePolling();
    
    // Add click handlers for message actions
    document.querySelectorAll('.mark-read-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const messageId = this.dataset.messageId;
            markMessageAsRead(messageId);
        });
    });
    
    document.querySelectorAll('.delete-message-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const messageId = this.dataset.messageId;
            deleteMessage(messageId);
        });
    });
}

// Export functions for global access
window.EduMate = {
    ajaxRequest,
    showNotification,
    formatDate,
    formatFileSize,
    rateContent,
    toggleBookmark,
    searchContent,
    updateUnreadCount,
    sendMessage,
    markMessageAsRead,
    deleteMessage,
    initializeMessageSystem
};

// Initialize message system when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeMessageSystem();
});