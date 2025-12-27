/**
 * Optimized File Upload System with Progress Tracking
 * Designed for low-resource servers (1C1G)
 */

class OptimizedUploader {
    constructor(options = {}) {
        this.options = {
            uploadUrl: '/content/upload-file',
            maxFileSize: 100 * 1024 * 1024, // 100MB
            chunkSize: 1024 * 1024, // 1MB chunks
            maxRetries: 3,
            retryDelay: 2000,
            timeoutMs: 300000, // 5 minutes
            ...options
        };
        
        this.activeUploads = new Map();
        this.queue = [];
        this.isProcessing = false;
    }

    /**
     * Initialize upload functionality
     */
    initialize() {
        this.setupFileInputValidation();
        this.setupDragAndDrop();
        this.setupUploadHandlers();
    }

    /**
     * Setup file input validation
     */
    setupFileInputValidation() {
        document.querySelectorAll('input[type="file"]').forEach(input => {
            input.addEventListener('change', (e) => {
                this.validateFile(e.target.files[0]);
            });
        });
    }

    /**
     * Setup drag and drop functionality
     */
    setupDragAndDrop() {
        const dropZones = document.querySelectorAll('.upload-drop-zone');
        
        dropZones.forEach(zone => {
            zone.addEventListener('dragover', (e) => {
                e.preventDefault();
                zone.classList.add('drag-over');
            });

            zone.addEventListener('dragleave', () => {
                zone.classList.remove('drag-over');
            });

            zone.addEventListener('drop', (e) => {
                e.preventDefault();
                zone.classList.remove('drag-over');
                
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    this.handleFileUpload(files[0]);
                }
            });
        });
    }

    /**
     * Setup upload handlers
     */
    setupUploadHandlers() {
        document.querySelectorAll('[data-upload-trigger]').forEach(trigger => {
            trigger.addEventListener('click', () => {
                const fileInput = document.querySelector(trigger.dataset.uploadTrigger);
                if (fileInput) {
                    fileInput.click();
                }
            });
        });
    }

    /**
     * Validate file before upload
     */
    validateFile(file) {
        if (!file) return false;

        if (file.size > this.options.maxFileSize) {
            this.showError(`文件大小超过限制 (${this.formatFileSize(this.options.maxFileSize)})`);
            return false;
        }

        // Add more validation as needed
        return true;
    }

    /**
     * Handle file upload with progress tracking
     */
    async handleFileUpload(file, onProgress = null, onComplete = null, onError = null) {
        if (!this.validateFile(file)) return;

        const uploadId = this.generateUploadId();
        const uploadData = {
            id: uploadId,
            file: file,
            startTime: Date.now(),
            retryCount: 0,
            onProgress: onProgress,
            onComplete: onComplete,
            onError: onError
        };

        this.activeUploads.set(uploadId, uploadData);
        
        try {
            const result = await this.uploadFile(uploadData);
            this.handleUploadSuccess(uploadId, result);
        } catch (error) {
            this.handleUploadError(uploadId, error);
        }
    }

    /**
     * Upload file with progress tracking
     */
    async uploadFile(uploadData) {
        const formData = new FormData();
        formData.append('file', uploadData.file);
        
        // Add content type if available
        const contentType = this.detectContentType(uploadData.file);
        if (contentType) {
            formData.append('content_type', contentType);
        }

        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            
            // Setup progress tracking
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    const percentComplete = Math.round((e.loaded / e.total) * 100);
                    const speed = this.calculateUploadSpeed(e.loaded, uploadData.startTime);
                    
                    if (uploadData.onProgress) {
                        uploadData.onProgress({
                            percent: percentComplete,
                            loaded: e.loaded,
                            total: e.total,
                            speed: speed,
                            timeElapsed: Date.now() - uploadData.startTime
                        });
                    }
                }
            });

            // Handle completion
            xhr.addEventListener('load', () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    try {
                        const response = JSON.parse(xhr.responseText);
                        if (response.success) {
                            resolve(response);
                        } else {
                            reject(new Error(response.error || 'Upload failed'));
                        }
                    } catch (e) {
                        reject(new Error('Invalid response from server'));
                    }
                } else {
                    reject(new Error(`HTTP ${xhr.status}: ${xhr.statusText}`));
                }
            });

            // Handle errors
            xhr.addEventListener('error', () => {
                reject(new Error('Network error during upload'));
            });

            xhr.addEventListener('timeout', () => {
                reject(new Error('Upload timeout'));
            });

            // Configure and send request
            xhr.open('POST', this.options.uploadUrl);
            xhr.timeout = this.options.timeoutMs;
            
            // Add CSRF token if available
            const csrfToken = this.getCSRFToken();
            if (csrfToken) {
                xhr.setRequestHeader('X-CSRFToken', csrfToken);
            }
            
            xhr.send(formData);
        });
    }

    /**
     * Handle upload success
     */
    handleUploadSuccess(uploadId, result) {
        const uploadData = this.activeUploads.get(uploadId);
        if (uploadData && uploadData.onComplete) {
            uploadData.onComplete(result);
        }
        
        this.activeUploads.delete(uploadId);
    }

    /**
     * Handle upload error with retry logic
     */
    async handleUploadError(uploadId, error) {
        const uploadData = this.activeUploads.get(uploadId);
        
        if (uploadData && uploadData.retryCount < this.options.maxRetries) {
            uploadData.retryCount++;
            
            console.warn(`Upload ${uploadId} failed, retrying (${uploadData.retryCount}/${this.options.maxRetries}):`, error);
            
            // Wait before retry
            await this.delay(this.options.retryDelay * uploadData.retryCount);
            
            try {
                const result = await this.uploadFile(uploadData);
                this.handleUploadSuccess(uploadId, result);
                return;
            } catch (retryError) {
                // Continue to error handling below
                console.error(`Retry ${uploadData.retryCount} failed:`, retryError);
            }
        }
        
        // Final error handling
        if (uploadData) {
            if (uploadData.onError) {
                uploadData.onError(error);
            }
            this.activeUploads.delete(uploadId);
        }
        
        this.showError(`上传失败: ${error.message}`);
    }

    /**
     * Detect content type from file
     */
    detectContentType(file) {
        const extension = file.name.split('.').pop().toLowerCase();
        
        const typeMap = {
            'mp4': 'video',
            'avi': 'video',
            'mov': 'video',
            'wmv': 'video',
            'flv': 'video',
            'webm': 'video',
            'mkv': 'video',
            'pdf': 'document',
            'doc': 'document',
            'docx': 'document',
            'txt': 'document',
            'rtf': 'document',
            'odt': 'document',
            'ppt': 'presentation',
            'pptx': 'presentation',
            'odp': 'presentation',
            'key': 'presentation'
        };
        
        return typeMap[extension] || 'document';
    }

    /**
     * Calculate upload speed
     */
    calculateUploadSpeed(bytesLoaded, startTime) {
        const timeElapsed = (Date.now() - startTime) / 1000; // seconds
        if (timeElapsed === 0) return 0;
        
        const bytesPerSecond = bytesLoaded / timeElapsed;
        return this.formatFileSize(bytesPerSecond) + '/s';
    }

    /**
     * Format file size for display
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    /**
     * Generate unique upload ID
     */
    generateUploadId() {
        return 'upload_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    /**
     * Get CSRF token
     */
    getCSRFToken() {
        const token = document.querySelector('meta[name="csrf-token"]');
        return token ? token.getAttribute('content') : null;
    }

    /**
     * Show error message
     */
    showError(message) {
        // Try to use existing alert system
        if (window.showAlert) {
            window.showAlert(message, 'danger');
        } else {
            // Fallback to console
            console.error('Upload error:', message);
            alert(message); // Last resort
        }
    }

    /**
     * Delay helper
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Cancel upload
     */
    cancelUpload(uploadId) {
        const uploadData = this.activeUploads.get(uploadId);
        if (uploadData) {
            this.activeUploads.delete(uploadId);
            if (uploadData.onError) {
                uploadData.onError(new Error('Upload cancelled'));
            }
        }
    }

    /**
     * Get upload statistics
     */
    getUploadStats() {
        return {
            activeUploads: this.activeUploads.size,
            queuedUploads: this.queue.length
        };
    }
}

// Initialize the uploader when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.optimizedUploader = new OptimizedUploader();
    window.optimizedUploader.initialize();
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = OptimizedUploader;
}