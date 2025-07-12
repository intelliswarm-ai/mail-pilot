// Mail Pilot Web Application JavaScript

// Global configuration
const Config = {
    API_BASE: '',
    POLLING_INTERVAL: 3000,
    STATUS_REFRESH_INTERVAL: 5000
};

// Utility functions
const Utils = {
    // Format date/time for display
    formatDateTime: (dateString) => {
        if (!dateString) return 'Never';
        const date = new Date(dateString);
        return date.toLocaleString();
    },

    // Format time ago
    timeAgo: (dateString) => {
        if (!dateString) return 'Never';
        const date = new Date(dateString);
        const now = new Date();
        const diff = now - date;
        
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);
        
        if (days > 0) return `${days} day${days > 1 ? 's' : ''} ago`;
        if (hours > 0) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
        if (minutes > 0) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
        return 'Just now';
    },

    // Show toast notification
    showToast: (message, type = 'info') => {
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        const container = document.getElementById('toast-container') || document.body;
        container.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Remove from DOM after hiding
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    },

    // Create loading button state
    setButtonLoading: (button, loading = true) => {
        if (loading) {
            button.dataset.originalText = button.innerHTML;
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
            button.disabled = true;
        } else {
            button.innerHTML = button.dataset.originalText || button.innerHTML;
            button.disabled = false;
        }
    },

    // Debounce function
    debounce: (func, wait) => {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
};

// API client
const API = {
    // Generic API call
    call: async (endpoint, options = {}) => {
        try {
            const response = await fetch(Config.API_BASE + endpoint, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API call failed:', error);
            throw error;
        }
    },

    // Process emails
    processEmails: () => API.call('/api/process-emails', { method: 'POST' }),
    
    // Get status
    getStatus: () => API.call('/api/status'),
    
    // Test Ollama connection
    testOllama: () => API.call('/api/test-ollama')
};

// Status management
const StatusManager = {
    currentStatus: null,
    updateCallbacks: [],

    // Add callback for status updates
    onUpdate: (callback) => {
        StatusManager.updateCallbacks.push(callback);
    },

    // Update status and notify callbacks
    update: (status) => {
        StatusManager.currentStatus = status;
        StatusManager.updateCallbacks.forEach(callback => {
            try {
                callback(status);
            } catch (error) {
                console.error('Status update callback failed:', error);
            }
        });
    },

    // Fetch and update status
    refresh: async () => {
        try {
            const status = await API.getStatus();
            StatusManager.update(status);
            return status;
        } catch (error) {
            console.error('Failed to refresh status:', error);
            Utils.showToast('Failed to refresh status', 'warning');
            return null;
        }
    }
};

// Email processing management
const EmailProcessor = {
    isProcessing: false,
    pollInterval: null,

    // Start email processing
    start: async () => {
        if (EmailProcessor.isProcessing) {
            Utils.showToast('Email processing already in progress', 'warning');
            return;
        }

        try {
            const result = await API.processEmails();
            EmailProcessor.isProcessing = true;
            
            Utils.showToast('Email processing started', 'success');
            
            // Start polling for updates
            EmailProcessor.startPolling();
            
            return result;
        } catch (error) {
            Utils.showToast('Failed to start email processing: ' + error.message, 'danger');
            throw error;
        }
    },

    // Start polling for status updates
    startPolling: () => {
        if (EmailProcessor.pollInterval) {
            clearInterval(EmailProcessor.pollInterval);
        }

        EmailProcessor.pollInterval = setInterval(async () => {
            const status = await StatusManager.refresh();
            
            if (status && !status.running) {
                EmailProcessor.stop();
                
                if (status.last_result) {
                    if (status.last_result.success) {
                        Utils.showToast('Email processing completed successfully!', 'success');
                    } else {
                        Utils.showToast('Email processing failed: ' + (status.error || 'Unknown error'), 'danger');
                    }
                }
            }
        }, Config.POLLING_INTERVAL);
    },

    // Stop processing and polling
    stop: () => {
        EmailProcessor.isProcessing = false;
        
        if (EmailProcessor.pollInterval) {
            clearInterval(EmailProcessor.pollInterval);
            EmailProcessor.pollInterval = null;
        }
    }
};

// Form validation helpers
const FormValidator = {
    // Validate email address
    validateEmail: (email) => {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    },

    // Validate URL
    validateUrl: (url) => {
        try {
            new URL(url);
            return true;
        } catch {
            return false;
        }
    },

    // Validate required fields
    validateRequired: (form) => {
        const required = form.querySelectorAll('[required]');
        let isValid = true;
        
        required.forEach(field => {
            if (!field.value.trim()) {
                field.classList.add('is-invalid');
                isValid = false;
            } else {
                field.classList.remove('is-invalid');
            }
        });
        
        return isValid;
    }
};

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    console.log('Mail Pilot Web App initialized');
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Add fade-in animation to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        setTimeout(() => {
            card.classList.add('fade-in');
        }, index * 100);
    });

    // Form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!FormValidator.validateRequired(form)) {
                event.preventDefault();
                event.stopPropagation();
                Utils.showToast('Please fill in all required fields', 'warning');
            }
        });

        // Real-time validation
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                if (input.hasAttribute('required') && !input.value.trim()) {
                    input.classList.add('is-invalid');
                } else {
                    input.classList.remove('is-invalid');
                }
            });
        });
    });

    // Page-specific initialization
    const page = document.body.dataset.page;
    if (page) {
        switch (page) {
            case 'dashboard':
                initDashboard();
                break;
            case 'setup':
                initSetup();
                break;
            case 'register':
                initRegister();
                break;
        }
    }
});

// Dashboard-specific initialization
function initDashboard() {
    console.log('Initializing dashboard');
    
    // Initial status refresh
    StatusManager.refresh();
    
    // Set up auto-refresh
    setInterval(() => {
        if (!EmailProcessor.isProcessing) {
            StatusManager.refresh();
        }
    }, Config.STATUS_REFRESH_INTERVAL);
}

// Setup page initialization
function initSetup() {
    console.log('Initializing setup page');
    
    // Auto-test Ollama connection
    setTimeout(() => {
        const testButton = document.getElementById('test-ollama');
        if (testButton) {
            testButton.click();
        }
    }, 1000);
}

// Register page initialization
function initRegister() {
    console.log('Initializing register page');
    
    // Prerequisites checklist logic is already in the template
}

// Global error handler
window.addEventListener('error', function(event) {
    console.error('Global error:', event.error);
    Utils.showToast('An unexpected error occurred', 'danger');
});

// Global unhandled promise rejection handler
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    Utils.showToast('An unexpected error occurred', 'danger');
});

// Export globals for use in templates
window.MailPilot = {
    Utils,
    API,
    StatusManager,
    EmailProcessor,
    FormValidator
};