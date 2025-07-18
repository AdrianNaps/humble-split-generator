/**
 * Character Utilities
 * Pure functions for character data manipulation
 * These will work in both current setup and React without changes
 */

/**
 * Get CSS class for WoW class
 * @param {string} className - WoW class name
 * @returns {string} CSS class name
 */
function getClassColor(className) {
    const colorMap = {
        'Death Knight': 'class-death_knight',
        'Demon Hunter': 'class-demon_hunter',
        'Druid': 'class-druid',
        'Evoker': 'class-evoker',
        'Hunter': 'class-hunter',
        'Mage': 'class-mage',
        'Monk': 'class-monk',
        'Paladin': 'class-paladin',
        'Priest': 'class-priest',
        'Rogue': 'class-rogue',
        'Shaman': 'class-shaman',
        'Warlock': 'class-warlock',
        'Warrior': 'class-warrior'
    };
    return colorMap[className] || 'class-default';
}

/**
 * Get role icon emoji
 * @param {string} role - Raid role
 * @returns {string} Role icon
 */
function getRoleIcon(role) {
    const iconMap = {
        'tank': '🛡️',
        'healer': '💚',
        'mdps': '⚔️',
        'rdps': '🏹'
    };
    return iconMap[role] || '⚡';
}

/**
 * Format role for display
 * @param {string} role - Raw role string
 * @returns {string} Formatted role
 */
function formatRole(role) {
    const roleMap = {
        'tank': 'Tank',
        'healer': 'Healer',
        'mdps': 'Melee DPS',
        'rdps': 'Ranged DPS'
    };
    return roleMap[role] || role;
}

/**
 * Sort characters by multiple criteria
 * @param {Array} characters - Array of character objects
 * @param {string} primarySort - Primary sort field
 * @param {string} secondarySort - Secondary sort field
 * @returns {Array} Sorted characters
 */
function sortCharacters(characters, primarySort = 'role', secondarySort = 'priority') {
    const roleOrder = { 'tank': 1, 'healer': 2, 'mdps': 3, 'rdps': 4 };
    const priorityOrder = { 'main': 1, 'alt': 2, 'helper': 3, 'inactive': 4 };

    return [...characters].sort((a, b) => {
        // Primary sort
        let primaryA, primaryB;
        if (primarySort === 'role') {
            primaryA = roleOrder[a.role_raid] || 5;
            primaryB = roleOrder[b.role_raid] || 5;
        } else if (primarySort === 'priority') {
            primaryA = priorityOrder[a.role_group] || 5;
            primaryB = priorityOrder[a.role_group] || 5;
        } else if (primarySort === 'name') {
            primaryA = a.name?.toLowerCase() || '';
            primaryB = b.name?.toLowerCase() || '';
        } else if (primarySort === 'class') {
            primaryA = a.class_name?.toLowerCase() || '';
            primaryB = b.class_name?.toLowerCase() || '';
        }

        if (primaryA !== primaryB) {
            return primaryA < primaryB ? -1 : 1;
        }

        // Secondary sort
        let secondaryA, secondaryB;
        if (secondarySort === 'role') {
            secondaryA = roleOrder[a.role_raid] || 5;
            secondaryB = roleOrder[b.role_raid] || 5;
        } else if (secondarySort === 'priority') {
            secondaryA = priorityOrder[a.role_group] || 5;
            secondaryB = priorityOrder[b.role_group] || 5;
        } else if (secondarySort === 'name') {
            secondaryA = a.name?.toLowerCase() || '';
            secondaryB = b.name?.toLowerCase() || '';
        }

        return secondaryA < secondaryB ? -1 : secondaryA > secondaryB ? 1 : 0;
    });
}

/**
 * Filter characters by criteria
 * @param {Array} characters - Array of character objects
 * @param {Object} filters - Filter criteria
 * @returns {Array} Filtered characters
 */
function filterCharacters(characters, filters) {
    return characters.filter(char => {
        // Role filter
        if (filters.role && char.role_raid !== filters.role) {
            return false;
        }

        // Priority filter
        if (filters.priority && char.role_group !== filters.priority) {
            return false;
        }

        // Class filter
        if (filters.className && char.class_name !== filters.className) {
            return false;
        }

        // Search filter (name or spec)
        if (filters.search) {
            const searchTerm = filters.search.toLowerCase();
            const name = char.name?.toLowerCase() || '';
            const spec = char.spec_name?.toLowerCase() || '';
            const className = char.class_name?.toLowerCase() || '';

            if (!name.includes(searchTerm) && 
                !spec.includes(searchTerm) && 
                !className.includes(searchTerm)) {
                return false;
            }
        }

        return true;
    });
}

/**
 * Get character statistics
 * @param {Array} characters - Array of character objects
 * @returns {Object} Character statistics
 */
function getCharacterStats(characters) {
    const stats = {
        total: characters.length,
        byRole: {},
        byPriority: {},
        byClass: {},
        byArmorType: {},
        byTierToken: {}
    };

    characters.forEach(char => {
        // Role distribution
        const role = char.role_raid;
        stats.byRole[role] = (stats.byRole[role] || 0) + 1;

        // Priority distribution
        const priority = char.role_group;
        stats.byPriority[priority] = (stats.byPriority[priority] || 0) + 1;

        // Class distribution
        const className = char.class_name;
        stats.byClass[className] = (stats.byClass[className] || 0) + 1;

        // Armor type distribution
        const armorType = char.armor_type;
        if (armorType) {
            stats.byArmorType[armorType] = (stats.byArmorType[armorType] || 0) + 1;
        }

        // Tier token distribution
        const tierToken = char.tier_token;
        if (tierToken) {
            stats.byTierToken[tierToken] = (stats.byTierToken[tierToken] || 0) + 1;
        }
    });

    return stats;
}

/**
 * Create character element for DOM insertion
 * @param {Object} character - Character data
 * @returns {HTMLElement} Character element
 */
function createCharacterElement(character) {
    const charDiv = document.createElement('div');
    charDiv.className = 'character-card';
    
    // Add data attributes for filtering/sorting
    charDiv.dataset.characterId = character.name;
    charDiv.dataset.role = character.role_raid;
    charDiv.dataset.priority = character.role_group;
    charDiv.dataset.className = character.class_name;
    
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
        <div class="character-priority-badge priority-${character.role_group}">
            ${character.role_group}
        </div>
    `;
    
    // Add click handler for character details
    charDiv.addEventListener('click', () => {
        showCharacterTooltip(character, charDiv);
    });
    
    return charDiv;
}

/**
 * Show character tooltip with details
 * @param {Object} character - Character data
 * @param {HTMLElement} targetElement - Element to position tooltip near
 */
function showCharacterTooltip(character, targetElement) {
    // Remove any existing tooltips
    const existingTooltips = document.querySelectorAll('.character-tooltip');
    existingTooltips.forEach(tooltip => tooltip.remove());

    // Create tooltip
    const tooltip = document.createElement('div');
    tooltip.className = 'character-tooltip';
    tooltip.style.cssText = `
        position: fixed;
        background: #333;
        color: white;
        padding: 12px;
        border-radius: 8px;
        font-size: 14px;
        z-index: 1000;
        max-width: 250px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        pointer-events: none;
    `;
    
    tooltip.innerHTML = `
        <div style="font-weight: bold; margin-bottom: 8px;">${character.name}</div>
        <div style="margin-bottom: 4px;">${character.spec_name} ${character.class_name}</div>
        <div style="margin-bottom: 4px;">Role: ${formatRole(character.role_raid)}</div>
        <div style="margin-bottom: 4px;">Priority: ${character.role_group}</div>
        ${character.armor_type ? `<div style="margin-bottom: 4px;">Armor: ${character.armor_type}</div>` : ''}
        ${character.tier_token ? `<div>Tier Token: ${character.tier_token}</div>` : ''}
        ${character.buffs && character.buffs.length > 0 ? 
            `<div style="margin-top: 8px; font-size: 12px; color: #ccc;">Buffs: ${character.buffs.join(', ')}</div>` : ''}
    `;
    
    // Position tooltip
    document.body.appendChild(tooltip);
    const rect = targetElement.getBoundingClientRect();
    
    // Position to the right of the element, or left if not enough space
    let left = rect.right + 10;
    if (left + tooltip.offsetWidth > window.innerWidth) {
        left = rect.left - tooltip.offsetWidth - 10;
    }
    
    let top = rect.top;
    if (top + tooltip.offsetHeight > window.innerHeight) {
        top = window.innerHeight - tooltip.offsetHeight - 10;
    }
    
    tooltip.style.left = `${left}px`;
    tooltip.style.top = `${top}px`;
    
    // Remove after delay
    setTimeout(() => {
        if (tooltip.parentNode) {
            tooltip.parentNode.removeChild(tooltip);
        }
    }, 3000);
}

/**
 * Validate character object
 * @param {Object} character - Character to validate
 * @returns {Object} Validation result
 */
function validateCharacter(character) {
    const errors = [];
    
    if (!character.name || typeof character.name !== 'string') {
        errors.push('Character name is required');
    }
    
    if (!character.class_name || typeof character.class_name !== 'string') {
        errors.push('Class name is required');
    }
    
    if (!character.spec_name || typeof character.spec_name !== 'string') {
        errors.push('Spec name is required');
    }
    
    if (!character.role_raid || !['tank', 'healer', 'mdps', 'rdps'].includes(character.role_raid)) {
        errors.push('Valid role_raid is required');
    }
    
    if (!character.role_group || !['main', 'alt', 'helper', 'inactive'].includes(character.role_group)) {
        errors.push('Valid role_group is required');
    }
    
    return {
        isValid: errors.length === 0,
        errors
    };
}

// Export for global access (until React migration)
window.getClassColor = getClassColor;
window.getRoleIcon = getRoleIcon;
window.formatRole = formatRole;
window.sortCharacters = sortCharacters;
window.filterCharacters = filterCharacters;
window.getCharacterStats = getCharacterStats;
window.createCharacterElement = createCharacterElement;
window.showCharacterTooltip = showCharacterTooltip;
window.validateCharacter = validateCharacter;