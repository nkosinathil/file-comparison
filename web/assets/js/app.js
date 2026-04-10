/**
 * Aurex - Main JavaScript
 */

// Global App Object
const AurexApp = {
    apiBaseUrl: '/api',
    wsBaseUrl: window.location.protocol === 'https:' ? 'wss://' : 'ws://' + window.location.host,
    
    // Show loading spinner
    showLoading(element) {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        if (element) {
            element.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Loading...';
            element.disabled = true;
        }
    },
    
    // Hide loading spinner
    hideLoading(element, text) {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        if (element) {
            element.innerHTML = text;
            element.disabled = false;
        }
    },
    
    // Show toast notification
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
        toast.style.zIndex = '9999';
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 5000);
    },
    
    // Format file size
    formatFileSize(bytes) {
        const units = ['B', 'KB', 'MB', 'GB', 'TB'];
        let size = bytes;
        let unitIndex = 0;
        
        while (size >= 1024 && unitIndex < units.length - 1) {
            size /= 1024;
            unitIndex++;
        }
        
        return `${size.toFixed(2)} ${units[unitIndex]}`;
    },
    
    // Format date/time
    formatDateTime(dateString) {
        const date = new Date(dateString);
        return date.toLocaleString();
    },
    
    // Confirm dialog
    confirm(message, callback) {
        if (window.confirm(message)) {
            callback();
        }
    }
};

// WebSocket Connection Manager
class WebSocketManager {
    constructor(url) {
        this.url = url;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.messageHandlers = [];
    }
    
    connect() {
        try {
            this.ws = new WebSocket(this.url);
            
            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.reconnectAttempts = 0;
                this.updateStatus('connected');
            };
            
            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.messageHandlers.forEach(handler => handler(data));
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateStatus('disconnected');
            };
            
            this.ws.onclose = () => {
                console.log('WebSocket closed');
                this.updateStatus('disconnected');
                this.attemptReconnect();
            };
        } catch (error) {
            console.error('WebSocket connection error:', error);
            this.updateStatus('disconnected');
        }
    }
    
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
    
    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        }
    }
    
    onMessage(handler) {
        this.messageHandlers.push(handler);
    }
    
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            this.updateStatus('connecting');
            console.log(`Reconnecting... Attempt ${this.reconnectAttempts}`);
            setTimeout(() => this.connect(), this.reconnectDelay * this.reconnectAttempts);
        }
    }
    
    updateStatus(status) {
        const statusElements = document.querySelectorAll('.ws-status');
        statusElements.forEach(el => {
            el.className = `ws-status ${status}`;
        });
    }
}

// File Upload Handler
class FileUploadHandler {
    constructor(inputElement, options = {}) {
        this.input = inputElement;
        this.options = Object.assign({
            maxFileSize: 50 * 1024 * 1024, // 50MB
            allowedTypes: ['application/pdf'],
            onSelect: null,
            onError: null
        }, options);
        
        this.init();
    }
    
    init() {
        this.input.addEventListener('change', (e) => this.handleFiles(e.target.files));
    }
    
    handleFiles(files) {
        const validFiles = [];
        
        for (let file of files) {
            if (!this.validateFile(file)) {
                continue;
            }
            validFiles.push(file);
        }
        
        if (this.options.onSelect && validFiles.length > 0) {
            this.options.onSelect(validFiles);
        }
    }
    
    validateFile(file) {
        if (file.size > this.options.maxFileSize) {
            const error = `File ${file.name} is too large. Maximum size is ${AurexApp.formatFileSize(this.options.maxFileSize)}`;
            if (this.options.onError) {
                this.options.onError(error);
            } else {
                AurexApp.showToast(error, 'danger');
            }
            return false;
        }
        
        if (!this.options.allowedTypes.includes(file.type)) {
            const error = `File ${file.name} is not a valid PDF file`;
            if (this.options.onError) {
                this.options.onError(error);
            } else {
                AurexApp.showToast(error, 'danger');
            }
            return false;
        }
        
        return true;
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Auto-dismiss alerts
    setTimeout(() => {
        const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(alert => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
});

// Export for use in other scripts
window.AurexApp = AurexApp;
window.WebSocketManager = WebSocketManager;
window.FileUploadHandler = FileUploadHandler;
