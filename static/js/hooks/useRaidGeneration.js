/**
 * useRaidGeneration Hook - FIXED VERSION
 * Manages raid generation state and API calls with character locking support
 */

// Generation state (will become React state)
let generationState = {
    isGenerating: false,
    hasGenerated: false,
    currentGroups: [],
    lastError: null,
    lastGeneratedAt: null
};

// Generation listeners
const generationListeners = new Set();

/**
 * Raid generation hook interface
 * @returns {Object} Generation state and methods
 */
function useRaidGeneration() {
    return {
        state: { ...generationState },
        generateGroups,
        clearGroups,
        regenerateGroups,
        subscribe: subscribeToGeneration,
        unsubscribe: unsubscribeFromGeneration
    };
}

/**
 * Generate raid groups with current settings and character locks
 * @returns {Promise<boolean>} Success status
 */
async function generateGroups() {
    if (generationState.isGenerating) {
        console.warn('Generation already in progress');
        return false;
    }

    // Update state
    updateGenerationState({
        isGenerating: true,
        lastError: null
    });

    try {
        // Get current settings
        const { settings } = useRaidSettings();
        
        // FIXED: Get character locks from RaidGroups component
        const characterLocks = window.raidGroups ? window.raidGroups.getCharacterLocks() : [];
        
        console.log('🔒 Sending character locks:', characterLocks);
        
        // Call API with locks
        const response = await fetch('/api/generate-splits', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                num_groups: settings.numberOfSplits,
                healers_per_group: settings.healersPerSplit,
                group_size: 30,
                character_locks: characterLocks  // FIXED: Include character locks
            })
        });

        const data = await response.json();

        if (data.success) {
            // Update state with success
            updateGenerationState({
                isGenerating: false,
                hasGenerated: true,
                currentGroups: data.groups,
                lastGeneratedAt: new Date()
            });

            console.log('✅ Raid splits generated successfully with locks applied');
            return true;
        } else {
            throw new Error(data.error || 'Failed to generate splits');
        }

    } catch (error) {
        // Update state with error
        updateGenerationState({
            isGenerating: false,
            lastError: error.message
        });

        console.error('❌ Error generating splits:', error);
        return false;
    }
}

/**
 * Clear current raid groups
 */
function clearGroups() {
    updateGenerationState({
        hasGenerated: false,
        currentGroups: [],
        lastError: null,
        lastGeneratedAt: null
    });
}

/**
 * Regenerate groups with current settings
 * @returns {Promise<boolean>} Success status
 */
async function regenerateGroups() {
    clearGroups();
    return await generateGroups();
}

/**
 * Update generation state
 * @param {Object} newState - Partial state to update
 */
function updateGenerationState(newState) {
    generationState = { ...generationState, ...newState };
    notifyGenerationListeners();
}

/**
 * Subscribe to generation state changes
 * @param {Function} listener - Function to call on changes
 */
function subscribeToGeneration(listener) {
    generationListeners.add(listener);
}

/**
 * Unsubscribe from generation changes
 * @param {Function} listener - Listener to remove
 */
function unsubscribeFromGeneration(listener) {
    generationListeners.delete(listener);
}

/**
 * Notify all listeners of generation state changes
 */
function notifyGenerationListeners() {
    generationListeners.forEach(listener => {
        try {
            listener(generationState);
        } catch (error) {
            console.error('Error in generation listener:', error);
        }
    });
}

/**
 * Get statistics about current groups
 * @returns {Object} Group statistics
 */
function getGroupStatistics() {
    if (!generationState.currentGroups.length) {
        return null;
    }

    const stats = {
        totalGroups: generationState.currentGroups.length,
        totalCharacters: 0,
        averageGroupSize: 0,
        roleDistribution: { tanks: 0, healers: 0, dps: 0 },
        priorityDistribution: { main: 0, alt: 0, helper: 0, inactive: 0 }
    };

    generationState.currentGroups.forEach(group => {
        stats.totalCharacters += group.total_members;
        stats.roleDistribution.tanks += group.tanks;
        stats.roleDistribution.healers += group.healers;
        stats.roleDistribution.dps += group.dps;

        // Count priority distribution
        group.characters.forEach(char => {
            if (stats.priorityDistribution[char.role_group] !== undefined) {
                stats.priorityDistribution[char.role_group]++;
            }
        });
    });

    stats.averageGroupSize = Math.round(stats.totalCharacters / stats.totalGroups);

    return stats;
}

// Export for global access (until React migration)
window.useRaidGeneration = useRaidGeneration;
window.generateGroups = generateGroups;
window.clearGroups = clearGroups;
window.regenerateGroups = regenerateGroups;
window.getGroupStatistics = getGroupStatistics;