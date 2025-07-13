/**
 * Mail Pilot JavaScript Utilities
 * Provides common functionality for the web interface
 */

// Global configuration
const MailPilot = {
    config: {
        apiTimeout: 30000,
        pollInterval: 2000,
        maxRetries: 3,
        toastDuration: 5000
    },
    
    state: {
        isProcessing: false,
        pollTimer: null,
        activeToasts: new Set()
    }
};

/**
 * Enhanced API helper with retry logic and better error handling
 */
async function apiCall(url, options = {}) {
    let attempt = 0;
    const maxRetries = MailPilot.config.maxRetries;
    
    while (attempt < maxRetries) {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), MailPilot.config.apiTimeout);
            
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                signal: controller.signal,
                ...options
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            return data;
            
        } catch (error) {
            attempt++;
            console.warn(`API call attempt ${attempt} failed:`, error);
            
            if (attempt >= maxRetries) {
                console.error('API call failed after all retries:', error);
                showToast(`API call failed: ${error.message}`, 'error');
                throw error;
            }
            
            // Exponential backoff
            await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000));
        }
    }
}

/**
 * Enhanced toast notification system
 */
function showToast(message, type = 'info', duration = null) {
    const toastId = `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const toastDuration = duration || MailPilot.config.toastDuration;
    
    const bgClass = {
        'error': 'bg-danger',
        'success': 'bg-success',
        'warning': 'bg-warning',
        'info': 'bg-primary'
    }[type] || 'bg-primary';
    
    const icon = {
        'error': 'fas fa-exclamation-triangle',
        'success': 'fas fa-check-circle',
        'warning': 'fas fa-exclamation-circle',
        'info': 'fas fa-info-circle'
    }[type] || 'fas fa-info-circle';
    
    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center text-white ${bgClass} border-0" role="alert" data-bs-autohide="false">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="${icon} me-2"></i>${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    const toastContainer = document.querySelector('.toast-container');
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement);
    
    MailPilot.state.activeToasts.add(toastId);
    
    // Auto-hide after duration
    setTimeout(() => {
        if (MailPilot.state.activeToasts.has(toastId)) {
            toast.hide();
        }
    }, toastDuration);
    
    // Clean up when hidden
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
        MailPilot.state.activeToasts.delete(toastId);
    });
    
    toast.show();
    return toast;
}

/**
 * Progress management
 */
function showProgress() {
    const container = document.getElementById('progressContainer');
    if (container) {
        container.style.display = 'block';
        container.classList.add('fade-in');
    }
    MailPilot.state.isProcessing = true;
}

function hideProgress() {
    const container = document.getElementById('progressContainer');
    if (container) {
        container.style.display = 'none';
        container.classList.remove('fade-in');
    }
    MailPilot.state.isProcessing = false;
}

function updateProgress(percent, status) {
    const progressBar = document.getElementById('progressBar');
    const progressPercent = document.getElementById('progressPercent');
    const progressStatus = document.getElementById('progressStatus');
    
    if (progressBar) {
        progressBar.style.width = `${percent}%`;
        progressBar.setAttribute('aria-valuenow', percent);
    }
    
    if (progressPercent) {
        progressPercent.textContent = `${percent}%`;
    }
    
    if (progressStatus) {
        progressStatus.textContent = status;
    }
}

/**
 * Enhanced polling with exponential backoff on errors
 */
function pollProcessingStatus() {
    let errorCount = 0;
    const maxErrors = 5;
    
    const poll = async () => {
        try {
            const status = await apiCall('/api/processing-status');
            errorCount = 0; // Reset error count on success
            
            if (status.is_running) {
                showProgress();
                updateProgress(status.progress || 0, status.current_step || 'Processing...');
            } else {
                hideProgress();
                
                if (MailPilot.state.pollTimer) {
                    clearInterval(MailPilot.state.pollTimer);
                    MailPilot.state.pollTimer = null;
                }
                
                if (status.status === 'completed') {
                    showToast('Email processing completed!', 'success');
                    setTimeout(() => window.location.reload(), 1000);
                } else if (status.status === 'error') {
                    showToast(`Processing failed: ${status.error}`, 'error');
                }
                
                return 'completed';
            }
        } catch (error) {
            errorCount++;
            console.error(`Status polling error (${errorCount}/${maxErrors}):`, error);
            
            if (errorCount >= maxErrors) {
                if (MailPilot.state.pollTimer) {
                    clearInterval(MailPilot.state.pollTimer);
                    MailPilot.state.pollTimer = null;
                }
                showToast('Lost connection to processing status', 'error');
                hideProgress();
            }
        }
    };
    
    // Start polling
    MailPilot.state.pollTimer = setInterval(poll, MailPilot.config.pollInterval);
    return MailPilot.state.pollTimer;
}

/**
 * Utility functions
 */
function formatDateTime(isoString) {
    try {
        return new Date(isoString).toLocaleString();
    } catch (error) {
        return 'Invalid date';
    }
}

function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(() => {
            showToast('Copied to clipboard!', 'success', 2000);
        }).catch(() => {
            fallbackCopyToClipboard(text);
        });
    } else {
        fallbackCopyToClipboard(text);
    }
}

function fallbackCopyToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        document.execCommand('copy');
        showToast('Copied to clipboard!', 'success', 2000);
    } catch (error) {
        showToast('Failed to copy to clipboard', 'error');
    }
    
    document.body.removeChild(textArea);
}

/**
 * Form validation utilities
 */
function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function validateRequired(value) {
    return value && value.trim().length > 0;
}

function addValidationFeedback(element, isValid, message = '') {
    element.classList.remove('is-valid', 'is-invalid');
    
    // Remove existing feedback
    const existingFeedback = element.parentNode.querySelector('.invalid-feedback, .valid-feedback');
    if (existingFeedback) {
        existingFeedback.remove();
    }
    
    if (isValid) {
        element.classList.add('is-valid');
    } else {
        element.classList.add('is-invalid');
        
        if (message) {
            const feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            feedback.textContent = message;
            element.parentNode.appendChild(feedback);
        }
    }
}

/**
 * Keyboard shortcuts
 */
function initKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Ctrl/Cmd + / for help
        if ((e.ctrlKey || e.metaKey) && e.key === '/') {
            e.preventDefault();
            showToast('Keyboard shortcuts: Ctrl+/ (help), Ctrl+R (refresh), Esc (close modals)', 'info', 8000);
        }
        
        // Escape to close modals
        if (e.key === 'Escape') {
            const openModals = document.querySelectorAll('.modal.show');
            openModals.forEach(modal => {
                const modalInstance = bootstrap.Modal.getInstance(modal);
                if (modalInstance) {
                    modalInstance.hide();
                }
            });
        }
        
        // Ctrl/Cmd + R for refresh (show confirmation)
        if ((e.ctrlKey || e.metaKey) && e.key === 'r' && MailPilot.state.isProcessing) {
            e.preventDefault();
            if (confirm('Processing is in progress. Are you sure you want to refresh?')) {
                window.location.reload();
            }
        }
    });
}

/**
 * Auto-save functionality
 */
function initAutoSave(formSelector, saveCallback, interval = 30000) {
    const form = document.querySelector(formSelector);
    if (!form) return;
    
    let lastSaved = '';
    
    const autoSave = () => {
        const formData = new FormData(form);
        const currentData = JSON.stringify(Object.fromEntries(formData));
        
        if (currentData !== lastSaved) {
            saveCallback(formData);
            lastSaved = currentData;
            showToast('Auto-saved', 'info', 1000);
        }
    };
    
    // Auto-save periodically
    setInterval(autoSave, interval);
    
    // Save before page unload
    window.addEventListener('beforeunload', (e) => {
        const formData = new FormData(form);
        const currentData = JSON.stringify(Object.fromEntries(formData));
        
        if (currentData !== lastSaved) {
            e.preventDefault();
            e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
            return e.returnValue;
        }
    });
}

/**
 * Initialize tooltips
 */
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize when DOM is ready
 */
document.addEventListener('DOMContentLoaded', function() {
    initKeyboardShortcuts();
    initTooltips();
    
    // Add loading states to buttons
    document.addEventListener('click', function(e) {
        if (e.target.matches('button[type="submit"]') || e.target.closest('button[type="submit"]')) {
            const button = e.target.matches('button') ? e.target : e.target.closest('button');
            const originalText = button.innerHTML;
            
            button.disabled = true;
            button.innerHTML = '<span class="loading-spinner"></span> ' + button.textContent.replace(/\s+/g, ' ').trim();
            
            // Re-enable after form submission
            setTimeout(() => {
                button.disabled = false;
                button.innerHTML = originalText;
            }, 3000);
        }
    });
    
    // Add smooth scrolling to anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href !== '#') {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });
    
    // Add fade-in animation to cards
    const cards = document.querySelectorAll('.card');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });
    
    cards.forEach(card => {
        observer.observe(card);
    });
});

/**
 * Export global functions
 */
window.MailPilot = MailPilot;
window.apiCall = apiCall;
window.showToast = showToast;
window.showProgress = showProgress;
window.hideProgress = hideProgress;
window.updateProgress = updateProgress;
window.pollProcessingStatus = pollProcessingStatus;
window.formatDateTime = formatDateTime;
window.copyToClipboard = copyToClipboard;
window.validateEmail = validateEmail;
window.validateRequired = validateRequired;
window.addValidationFeedback = addValidationFeedback;
window.initAutoSave = initAutoSave;