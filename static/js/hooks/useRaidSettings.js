/**
 * useRaidSettings Hook
 * Manages raid settings state and persistence
 * Future React Hook: Will become actual useState/useEffect
 */

// Settings state (will become React state)
let raidSettings = {
    numberOfSplits: 3,
    healersPerSplit: 5
};

// Settings change listeners (will become React state setters)
const settingsListeners = new Set();

/**
 * Get current raid settings
 * @returns {Object} Current settings
 */
function useRaidSettings() {
    return {
        settings: { ...raidSettings },
        updateSettings,
        resetSettings,
        validateSettings,
        subscribe: subscribeToSettings,
        unsubscribe: unsubscribeFromSettings
    };
}

/**
 * Update raid settings
 * @param {Object} newSettings - Partial settings to update
 * @returns {boolean} Success status
 */
function updateSettings(newSettings) {
    const validation = validateSettings(newSettings);
    if (!validation.isValid) {
        console.error('Invalid settings:', validation.errors);
        return false;
    }

    // Update settings
    raidSettings = { ...raidSettings, ...newSettings };
    
    // Notify listeners (will become React state updates)
    notifySettingsListeners();
    
    // Update UI displays
    updateSettingsDisplay();
    
    return true;
}

/**
 * Validate settings object
 * @param {Object} settings - Settings to validate
 * @returns {Object} Validation result
 */
function validateSettings(settings) {
    const errors = [];
    
    if (settings.numberOfSplits !== undefined) {
        if (settings.numberOfSplits < 2 || settings.numberOfSplits > 5) {
            errors.push('Number of splits must be between 2 and 5');
        }
    }
    
    if (settings.healersPerSplit !== undefined) {
        if (settings.healersPerSplit < 1 || settings.healersPerSplit > 8) {
            errors.push('Healers per split must be between 1 and 8');
        }
    }
    
    return {
        isValid: errors.length === 0,
        errors
    };
}

/**
 * Reset settings to defaults
 */
function resetSettings() {
    updateSettings({
        numberOfSplits: 3,
        healersPerSplit: 5
    });
}

/**
 * Subscribe to settings changes
 * @param {Function} listener - Function to call on changes
 */
function subscribeToSettings(listener) {
    settingsListeners.add(listener);
}

/**
 * Unsubscribe from settings changes
 * @param {Function} listener - Listener to remove
 */
function unsubscribeFromSettings(listener) {
    settingsListeners.delete(listener);
}

/**
 * Notify all listeners of settings changes
 */
function notifySettingsListeners() {
    settingsListeners.forEach(listener => {
        try {
            listener(raidSettings);
        } catch (error) {
            console.error('Error in settings listener:', error);
        }
    });
}

/**
 * Update UI elements that display current settings
 */
function updateSettingsDisplay() {
    const currentSplitsEl = document.getElementById('currentSplits');
    const currentHealersEl = document.getElementById('currentHealers');
    
    if (currentSplitsEl) {
        currentSplitsEl.textContent = raidSettings.numberOfSplits;
    }
    if (currentHealersEl) {
        currentHealersEl.textContent = raidSettings.healersPerSplit;
    }
}

/**
 * Load settings from form elements
 * @returns {Object} Settings from form
 */
function getSettingsFromForm() {
    const numberOfSplits = parseInt(document.getElementById('numberOfSplits')?.value);
    const healersPerSplit = parseInt(document.getElementById('healersPerSplit')?.value);
    
    return {
        numberOfSplits: isNaN(numberOfSplits) ? raidSettings.numberOfSplits : numberOfSplits,
        healersPerSplit: isNaN(healersPerSplit) ? raidSettings.healersPerSplit : healersPerSplit
    };
}

/**
 * Populate form with current settings
 */
function populateSettingsForm() {
    const numberOfSplitsEl = document.getElementById('numberOfSplits');
    const healersPerSplitEl = document.getElementById('healersPerSplit');
    
    if (numberOfSplitsEl) {
        numberOfSplitsEl.value = raidSettings.numberOfSplits;
    }
    if (healersPerSplitEl) {
        healersPerSplitEl.value = raidSettings.healersPerSplit;
    }
}

// Export for global access (until React migration)
window.useRaidSettings = useRaidSettings;
window.updateSettings = updateSettings;
window.resetSettings = resetSettings;
window.populateSettingsForm = populateSettingsForm;
window.getSettingsFromForm = getSettingsFromForm;