/**
 * RaidGroups Component Logic - FIXED VERSION
 * Handles raid group display and management
 */

class RaidGroups {
    constructor() {
        this.container = null;
        this.currentGroups = [];
        this.generationSubscription = null;
        // Initialize character locks storage
        this.characterLocks = new Map();
    }

    /**
     * Initialize the raid groups component
     */
    init() {
        this.container = document.getElementById('splitsContainer');
        if (!this.container) {
            console.error('Splits container element not found');
            return;
        }

        // Subscribe to generation state changes
        const { subscribe } = useRaidGeneration();
        this.generationSubscription = subscribe((state) => {
            this.handleGenerationStateChange(state);
        });

        console.log('✅ RaidGroups initialized with locking support');
    }

    /**
     * Handle generation state changes
     * @param {Object} state - Generation state
     */
    handleGenerationStateChange(state) {
        if (state.isGenerating) {
            this.showLoadingState();
        } else if (state.hasGenerated && state.currentGroups.length > 0) {
            this.renderGroups(state.currentGroups);
        } else if (state.lastError) {
            this.showErrorState(state.lastError);
        } else {
            this.showWelcomeState();
        }
    }

    /**
     * Generate raid groups - MAIN FUNCTION
     */
    async generateRaidSplits() {
        console.log('🎯 Starting raid group generation...');
        
        // Show loading on button
        const generateBtn = document.getElementById('generateBtn');
        const originalHTML = setButtonLoading(generateBtn, 'Generating...');
        
        try {
            // Use the generation hook
            const success = await generateGroups();
            
        } catch (error) {
            console.error('Error in generateRaidSplits:', error);
            showErrorMessage('Error generating groups: ' + error.message);
        } finally {
            // Restore button
            restoreButtonFromLoading(generateBtn, originalHTML);
        }
    }

    /**
     * Render raid groups
     * @param {Array} groups - Array of group data
     */
    renderGroups(groups) {
        this.currentGroups = groups;
        this.container.innerHTML = '';

        groups.forEach(group => {
            const groupElement = this.createGroupElement(group);
            this.container.appendChild(groupElement);
        });
    }

    /**
     * Create a single group element
     * @param {Object} group - Group data
     * @returns {HTMLElement} Group element
     */
    createGroupElement(group) {
        const groupDiv = document.createElement('div');
        groupDiv.className = 'group-container';
        groupDiv.dataset.groupId = group.group_id;

        // Create header
        const headerDiv = document.createElement('div');
        headerDiv.className = 'group-header';
        
        const titleDiv = document.createElement('h3');
        titleDiv.className = 'group-title';
        titleDiv.textContent = `Group ${group.group_id}`;
        
        const statsDiv = document.createElement('div');
        statsDiv.className = 'group-stats';
        
        // Create details button
        const detailsBtn = document.createElement('button');
        detailsBtn.className = 'group-details-btn';
        detailsBtn.title = 'View detailed analysis';
        detailsBtn.innerHTML = '<i class="fas fa-chart-line"></i> Details';
        detailsBtn.addEventListener('click', () => {
            openSplitDetailsModal(group, group.group_id, this.currentGroups.length);
        });
        
        // Create member count badge
        const statBadge = document.createElement('div');
        statBadge.className = 'stat-badge';
        statBadge.innerHTML = `
            <i class="fas fa-users"></i>
            <span>${group.total_members}</span>
        `;
        
        statsDiv.appendChild(detailsBtn);
        statsDiv.appendChild(statBadge);
        headerDiv.appendChild(titleDiv);
        headerDiv.appendChild(statsDiv);
        groupDiv.appendChild(headerDiv);

        // Create info section (rest of the method continues as before)
        const infoDiv = document.createElement('div');
        infoDiv.className = 'group-info';
        
        // Get armor distribution for mains
        const armorDist = group.armor_distribution_mains || {};
        const armorDisplay = `${armorDist.plate || 0}P / ${armorDist.mail || 0}M / ${armorDist.leather || 0}L / ${armorDist.cloth || 0}C`;
        
        // Get tier distribution for mains  
        const tierDist = group.tier_distribution_mains || {};
        const tierDisplay = `${tierDist.Zenith || 0}Z / ${tierDist.Dreadful || 0}D / ${tierDist.Mystic || 0}M / ${tierDist.Venerated || 0}V`;
        
        infoDiv.innerHTML = `
            <div class="group-info-row">
                <span class="group-info-label">Composition:</span>
                <span class="group-info-value">${group.tanks}T / ${group.healers}H / ${group.dps}D</span>
            </div>
            <div class="group-info-row">
                <span class="group-info-label">Main Characters:</span>
                <span class="group-info-value">${group.mains_count || 'N/A'}</span>
            </div>
            <div class="group-info-row">
                <span class="group-info-label">Armor (Mains):</span>
                <span class="group-info-value">${armorDisplay}</span>
            </div>
            <div class="group-info-row">
                <span class="group-info-label">Tier (Mains):</span>
                <span class="group-info-value">${tierDisplay}</span>
            </div>
        `;
        groupDiv.appendChild(infoDiv);

        // Create characters grid
        const charactersDiv = document.createElement('div');
        charactersDiv.className = 'characters-grid';

        // Sort and render characters
        const sortedCharacters = this.sortCharactersByRole(group.characters);
        sortedCharacters.forEach(character => {
            const charElement = this.createCharacterElement(character, group.group_id);
            charactersDiv.appendChild(charElement);
        });

        groupDiv.appendChild(charactersDiv);
        return groupDiv;
    }

    /**
     * Create character element with lock functionality
     * @param {Object} character - Character data
     * @param {number} groupId - Group ID this character is in
     * @returns {HTMLElement} Character element
     */
    createCharacterElement(character, groupId) {
        const charDiv = document.createElement('div');
        const isLocked = this.isCharacterLocked(character.name);
        
        charDiv.className = `character-card ${isLocked ? 'locked' : ''}`;
        charDiv.dataset.characterId = character.name;
        charDiv.dataset.role = character.role_raid;
        charDiv.dataset.priority = character.role_group;
        charDiv.dataset.className = character.class_name;
        charDiv.dataset.isLocked = isLocked;
        
        // Get class color and role icon
        const classColor = getClassColor(character.class_name);
        const roleIcon = getRoleIcon(character.role_raid);
        
        charDiv.innerHTML = `
            <div class="character-role-icon ${classColor}">
                ${roleIcon}
            </div>
            <div class="character-main-info">
                <div class="character-name-display">${character.name}</div>
                <div class="character-spec-class">${character.spec_name} ${character.class_name}</div>
            </div>
            <div class="character-priority-section">
                <button class="character-lock-btn ${isLocked ? 'locked' : 'unlocked'}" 
                        onclick="raidGroups.toggleCharacterLock('${character.name}', ${groupId}, this)"
                        title="${isLocked ? 'Click to unlock' : 'Click to lock in this group'}">
                    <i class="fas fa-${isLocked ? 'lock' : 'lock-open'}"></i>
                </button>
                <div class="character-priority-badge priority-${character.role_group}">
                    ${character.role_group}
                </div>
            </div>
        `;
        
        return charDiv;
    }

    /**
     * Sort characters by lock status first, then role
     * @param {Array} characters - Array of character objects
     * @returns {Array} Sorted characters
     */
    sortCharactersByRole(characters) {
        const roleOrder = { 'tank': 1, 'healer': 2, 'mdps': 3, 'rdps': 4 };
        const priorityOrder = { 'main': 1, 'alt': 2, 'helper': 3, 'inactive': 4 };

        return characters.sort((a, b) => {
            // Locked characters first
            const aLocked = this.isCharacterLocked(a.name);
            const bLocked = this.isCharacterLocked(b.name);
            
            if (aLocked && !bLocked) return -1;
            if (!aLocked && bLocked) return 1;

            // Then by role
            const roleA = roleOrder[a.role_raid] || 5;
            const roleB = roleOrder[b.role_raid] || 5;

            if (roleA !== roleB) {
                return roleA - roleB;
            }

            // Then by priority
            const priorityA = priorityOrder[a.role_group] || 5;
            const priorityB = priorityOrder[b.role_group] || 5;

            return priorityA - priorityB;
        });
    }

    /**
     * Check if character is locked
     * @param {string} characterName - Character name
     * @returns {boolean} Is locked
     */
    isCharacterLocked(characterName) {
        return this.characterLocks.has(characterName);
    }

    /**
     * Toggle character lock state
     * @param {string} characterName - Character name
     * @param {number} groupId - Group ID
     * @param {HTMLElement} buttonElement - Lock button
     */
    toggleCharacterLock(characterName, groupId, buttonElement) {
        const characterCard = buttonElement.closest('.character-card');
        const isCurrentlyLocked = this.characterLocks.has(characterName);
        
        if (isCurrentlyLocked) {
            // Unlock
            this.characterLocks.delete(characterName);
            
            buttonElement.classList.remove('locked');
            buttonElement.classList.add('unlocked');
            buttonElement.innerHTML = '<i class="fas fa-lock-open"></i>';
            buttonElement.title = 'Click to lock in this group';
            
            characterCard.classList.remove('locked');
            characterCard.dataset.isLocked = 'false';
            
        } else {
            // Lock
            this.characterLocks.set(characterName, groupId);
            
            buttonElement.classList.remove('unlocked');
            buttonElement.classList.add('locked');
            buttonElement.innerHTML = '<i class="fas fa-lock"></i>';
            buttonElement.title = 'Click to unlock';
            
            characterCard.classList.add('locked');
            characterCard.dataset.isLocked = 'true';
            
        }
        
        // Re-sort characters in this group
        this.sortCharactersInGroup(buttonElement.closest('.group-container'));
    }

    /**
     * Sort characters within a group container
     * @param {HTMLElement} groupContainer - Group container
     */
    sortCharactersInGroup(groupContainer) {
        const charactersGrid = groupContainer.querySelector('.characters-grid');
        if (!charactersGrid) return;
        
        const characterCards = Array.from(charactersGrid.querySelectorAll('.character-card'));
        
        characterCards.sort((a, b) => {
            const aLocked = a.dataset.isLocked === 'true';
            const bLocked = b.dataset.isLocked === 'true';
            
            // Locked first
            if (aLocked && !bLocked) return -1;
            if (!aLocked && bLocked) return 1;
            
            // Then by existing order
            return 0;
        });
        
        // Re-append
        characterCards.forEach(card => charactersGrid.appendChild(card));
    }

    /**
     * Get character locks for API
     * @returns {Array} Array of lock objects
     */
    getCharacterLocks() {
        const locks = [];
        this.characterLocks.forEach((groupId, characterName) => {
            locks.push({
                characterName: characterName,
                groupId: groupId
            });
        });
        return locks;
    }

    /**
     * Clear all character locks
     */
    clearAllLocks() {
        const lockedCount = this.characterLocks.size;
        this.characterLocks.clear();
        
        // Update all locked cards
        document.querySelectorAll('.character-card.locked').forEach(card => {
            const lockBtn = card.querySelector('.character-lock-btn');
            if (lockBtn) {
                lockBtn.classList.remove('locked');
                lockBtn.classList.add('unlocked');
                lockBtn.innerHTML = '<i class="fas fa-lock-open"></i>';
                lockBtn.title = 'Click to lock in this group';
            }
            
            card.classList.remove('locked');
            card.dataset.isLocked = 'false';
        });
        
    }

    /**
     * Show loading state
     */
    showLoadingState() {
        this.container.innerHTML = `
            <div class="welcome-container">
                <div class="welcome-icon">
                    <i class="fas fa-spinner fa-spin" style="font-size: 64px;"></i>
                </div>
                <h1 class="welcome-title">Generating Raid Groups</h1>
                <p class="welcome-subtitle">
                    Creating optimized groups based on your settings...
                </p>
            </div>
        `;
    }

    /**
     * Show welcome state
     */
    showWelcomeState() {
        this.container.innerHTML = `
            <div class="welcome-container" id="welcomeContainer">
                <div class="welcome-icon">🎲</div>
                <h1 class="welcome-title">Ready to Generate Raid Groups</h1>
                <p class="welcome-subtitle">
                    Click "Generate Splits" to create optimized raid groups based on your current settings.
                    The algorithm will balance roles, armor types, and tier tokens across all groups.
                </p>
            </div>
        `;
    }

    /**
     * Show error state
     * @param {string} error - Error message
     */
    showErrorState(error) {
        this.container.innerHTML = `
            <div class="welcome-container">
                <div class="welcome-icon">❌</div>
                <h1 class="welcome-title">Generation Failed</h1>
                <p class="welcome-subtitle">
                    ${error}
                </p>
                <button class="btn btn-primary" onclick="raidGroups.generateRaidSplits()">
                    <i class="fas fa-redo"></i>
                    Try Again
                </button>
            </div>
        `;
    }

    /**
     * Clear groups and show welcome state
     */
    clear() {
        clearGroups();
    }

    /**
     * Get current groups
     * @returns {Array} Current groups
     */
    getCurrentGroups() {
        return [...this.currentGroups];
    }
}

// Create global instance
const raidGroups = new RaidGroups();

// FIXED: Make the function available globally
function generateRaidSplits() {
    return raidGroups.generateRaidSplits();
}

function clearRaidGroups() {
    raidGroups.clear();
}

function regenerateGroups() {
    return raidGroups.generateRaidSplits();
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    raidGroups.init();
});

// Export for global access
window.RaidGroups = RaidGroups;
window.raidGroups = raidGroups;
window.generateRaidSplits = generateRaidSplits;
window.clearRaidGroups = clearRaidGroups;
window.regenerateGroups = regenerateGroups;