/**
 * UI Utilities
 * Pure functions for common UI operations
 * These will work in both current setup and React without changes
 */

/**
 * Show loading state on a button
 * @param {HTMLElement} button - Button element
 * @param {string} loadingText - Text to show while loading
 * @returns {string} Original button HTML for restoration
 */
function setButtonLoading(button, loadingText = 'Loading...') {
    if (!button) return '';
    
    const originalHTML = button.innerHTML;
    
    button.disabled = true;
    button.classList.add('loading');
    button.innerHTML = `<i class="fas fa-spinner fa-spin"></i> ${loadingText}`;
    
    return originalHTML;
}

/**
 * Restore button from loading state
 * @param {HTMLElement} button - Button element
 * @param {string} originalHTML - Original button HTML
 */
function restoreButtonFromLoading(button, originalHTML) {
    if (!button) return;
    
    button.disabled = false;
    button.classList.remove('loading');
    button.innerHTML = originalHTML;
}

/**
 * Show a temporary success message
 * @param {string} message - Success message to display
 * @param {number} duration - Duration in milliseconds (default: 3000)
 */
function showSuccessMessage(message, duration = 3000) {
    showMessage(message, 'success', duration);
}

/**
 * Show a temporary error message
 * @param {string} message - Error message to display
 * @param {number} duration - Duration in milliseconds (default: 5000)
 */
function showErrorMessage(message, duration = 5000) {
    showMessage(message, 'error', duration);
}

/**
 * Show a temporary info message
 * @param {string} message - Info message to display
 * @param {number} duration - Duration in milliseconds (default: 3000)
 */
function showInfoMessage(message, duration = 3000) {
    showMessage(message, 'info', duration);
}

/**
 * Show a temporary message
 * @param {string} message - Message to display
 * @param {string} type - Message type (success, error, info)
 * @param {number} duration - Duration in milliseconds
 */
function showMessage(message, type = 'info', duration = 3000) {
    // Create message element
    const messageDiv = document.createElement('div');
    messageDiv.className = `alert alert-${type === 'error' ? 'danger' : type} position-fixed`;
    messageDiv.style.cssText = `
        top: 20px; 
        right: 20px; 
        z-index: 9999; 
        min-width: 300px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        animation: slideInRight 0.3s ease;
    `;
    messageDiv.textContent = message;
    
    // Add close button
    const closeBtn = document.createElement('button');
    closeBtn.innerHTML = '×';
    closeBtn.className = 'btn-close';
    closeBtn.style.cssText = `
        background: none;
        border: none;
        font-size: 20px;
        float: right;
        margin-left: 10px;
        cursor: pointer;
        opacity: 0.7;
    `;
    closeBtn.addEventListener('click', () => removeMessage(messageDiv));
    
    messageDiv.appendChild(closeBtn);
    document.body.appendChild(messageDiv);
    
    // Auto-remove after duration
    setTimeout(() => removeMessage(messageDiv), duration);
}

/**
 * Remove a message element with animation
 * @param {HTMLElement} messageElement - Message element to remove
 */
function removeMessage(messageElement) {
    if (messageElement && messageElement.parentNode) {
        messageElement.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => {
            if (messageElement.parentNode) {
                messageElement.parentNode.removeChild(messageElement);
            }
        }, 300);
    }
}

/**
 * Smooth scroll to an element
 * @param {HTMLElement} element - Element to scroll to
 * @param {Object} options - Scroll options
 */
function smoothScrollTo(element, options = {}) {
    if (!element) return;
    
    const defaultOptions = {
        behavior: 'smooth',
        block: 'start',
        inline: 'nearest'
    };
    
    element.scrollIntoView({ ...defaultOptions, ...options });
}

/**
 * Debounce function to limit rapid function calls
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function} Debounced function
 */
function debounce(func, wait) {
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

/**
 * Throttle function to limit function calls to a specific interval
 * @param {Function} func - Function to throttle
 * @param {number} limit - Time limit in milliseconds
 * @returns {Function} Throttled function
 */
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * Check if an element is visible in the viewport
 * @param {HTMLElement} element - Element to check
 * @returns {boolean} True if element is visible
 */
function isElementVisible(element) {
    if (!element) return false;
    
    const rect = element.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

/**
 * Get element's position relative to viewport
 * @param {HTMLElement} element - Element to check
 * @returns {Object} Position information
 */
function getElementPosition(element) {
    if (!element) return null;
    
    const rect = element.getBoundingClientRect();
    return {
        top: rect.top,
        left: rect.left,
        bottom: rect.bottom,
        right: rect.right,
        width: rect.width,
        height: rect.height,
        centerX: rect.left + rect.width / 2,
        centerY: rect.top + rect.height / 2
    };
}

/**
 * Add CSS animation keyframes dynamically
 */
function addAnimationStyles() {
    if (document.getElementById('dynamic-animations')) return;
    
    const style = document.createElement('style');
    style.id = 'dynamic-animations';
    style.textContent = `
        @keyframes slideInRight {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        @keyframes slideOutRight {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        @keyframes fadeOut {
            from { opacity: 1; }
            to { opacity: 0; }
        }
        
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-5px); }
            75% { transform: translateX(5px); }
        }
    `;
    document.head.appendChild(style);
}

/**
 * Copy text to clipboard
 * @param {string} text - Text to copy
 * @returns {Promise<boolean>} Success status
 */
async function copyToClipboard(text) {
    try {
        if (navigator.clipboard && window.isSecureContext) {
            await navigator.clipboard.writeText(text);
            return true;
        } else {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'absolute';
            textArea.style.left = '-999999px';
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            return true;
        }
    } catch (error) {
        console.error('Failed to copy text:', error);
        return false;
    }
}

/**
 * Format number with separators
 * @param {number} number - Number to format
 * @returns {string} Formatted number
 */
function formatNumber(number) {
    return new Intl.NumberFormat().format(number);
}

/**
 * Format date for display
 * @param {Date} date - Date to format
 * @returns {string} Formatted date
 */
function formatDate(date) {
    return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(date);
}

// Initialize animations on load
document.addEventListener('DOMContentLoaded', addAnimationStyles);

// Export for global access (until React migration)
window.setButtonLoading = setButtonLoading;
window.restoreButtonFromLoading = restoreButtonFromLoading;
window.showSuccessMessage = showSuccessMessage;
window.showErrorMessage = showErrorMessage;
window.showInfoMessage = showInfoMessage;
window.smoothScrollTo = smoothScrollTo;
window.debounce = debounce;
window.throttle = throttle;
window.isElementVisible = isElementVisible;
window.getElementPosition = getElementPosition;
window.copyToClipboard = copyToClipboard;
window.formatNumber = formatNumber;
window.formatDate = formatDate;