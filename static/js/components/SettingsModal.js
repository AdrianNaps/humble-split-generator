/**
 * SettingsModal Component Logic
 * Handles settings modal interactions and form management
 * Future React Component: Will become actual React component
 */

class SettingsModal {
    constructor() {
        this.modalElement = null;
        this.isOpen = false;
        this.boundKeyHandler = this.handleKeyDown.bind(this);
        this.boundClickHandler = this.handleOverlayClick.bind(this);
    }

    /**
     * Initialize the settings modal
     */
    init() {
        this.modalElement = document.getElementById('settingsModal');
        if (!this.modalElement) {
            console.error('Settings modal element not found');
            return;
        }

        // Add event listeners
        this.addEventListeners();
        console.log('✅ SettingsModal initialized');
    }

    /**
     * Add event listeners for modal interactions
     */
    addEventListeners() {
        // Close button
        const closeBtn = this.modalElement.querySelector('.modal-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.close());
        }

        // Cancel button
        const cancelBtn = this.modalElement.querySelector('.btn-secondary');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.close());
        }

        // Save button
        const saveBtn = this.modalElement.querySelector('.btn-primary');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.save());
        }

        // Form submission
        const form = this.modalElement.querySelector('#settingsForm');
        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.save();
            });
        }
    }

    /**
     * Open the settings modal
     */
    open() {
        if (this.isOpen) return;

        // Populate form with current settings
        populateSettingsForm();

        // Show modal
        this.modalElement.classList.add('active');
        this.isOpen = true;

        // Add global event listeners
        document.addEventListener('keydown', this.boundKeyHandler);
        this.modalElement.addEventListener('click', this.boundClickHandler);

        // Focus first input
        const firstInput = this.modalElement.querySelector('input');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 100);
        }
    }

    /**
     * Close the settings modal
     */
    close() {
        if (!this.isOpen) return;

        // Hide modal
        this.modalElement.classList.remove('active');
        this.isOpen = false;

        // Remove global event listeners
        document.removeEventListener('keydown', this.boundKeyHandler);
        this.modalElement.removeEventListener('click', this.boundClickHandler);
    }

    /**
     * Save settings from form
     */
    save() {
        try {
            // Get settings from form
            const formSettings = getSettingsFromForm();
            
            // Update settings (this validates and updates)
            const success = updateSettings(formSettings);
            
            if (success) {
                this.close();
                showSuccessMessage('Settings saved successfully!');
            } else {
                showErrorMessage('Invalid settings. Please check your values.');
            }
        } catch (error) {
            console.error('Error saving settings:', error);
            showErrorMessage('Error saving settings: ' + error.message);
        }
    }

    /**
     * Handle keyboard events
     * @param {KeyboardEvent} event - Keyboard event
     */
    handleKeyDown(event) {
        if (event.key === 'Escape' && this.isOpen) {
            this.close();
        }
    }

    /**
     * Handle overlay clicks (close on outside click)
     * @param {MouseEvent} event - Click event
     */
    handleOverlayClick(event) {
        if (event.target === this.modalElement) {
            this.close();
        }
    }

    /**
     * Check if modal is currently open
     * @returns {boolean} Open status
     */
    isModalOpen() {
        return this.isOpen;
    }
}

// Create global instance
const settingsModal = new SettingsModal();

// Global functions for backward compatibility
function openSettingsModal() {
    settingsModal.open();
}

function closeSettingsModal() {
    settingsModal.close();
}

function saveSettings() {
    settingsModal.save();
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    settingsModal.init();
});

// Export for global access
window.SettingsModal = SettingsModal;
window.settingsModal = settingsModal;
window.openSettingsModal = openSettingsModal;
window.closeSettingsModal = closeSettingsModal;
window.saveSettings = saveSettings;