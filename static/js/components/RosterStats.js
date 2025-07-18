/**
 * RosterStats Component Logic
 * Handles roster statistics display and calculations
 */

class RosterStats {
    constructor() {
        this.isExpanded = false;
        this.container = null;
        this.statsData = {
            roleGroups: {
                main: 0,
                alt: 0,
                helper: 0
            },
            mains: {
                tokens: { Zenith: 0, Dreadful: 0, Mystic: 0, Venerated: 0 },
                armor: { plate: 0, mail: 0, leather: 0, cloth: 0 }
            },
            all: {
                raidBuffs: {}
            }
        };
    }

    /**
     * Initialize the roster stats component
     */
    init() {
        this.container = document.querySelector('.roster-stats-container');
        if (!this.container) {
            console.error('Roster stats container not found');
            return;
        }

        // Add click handler to the header
        const header = document.getElementById('rosterStatsHeader');
        if (header) {
            header.addEventListener('click', () => this.toggle());
        } else {
            console.error('Roster stats header not found');
        }

        // Load saved state
        this.loadExpandedState();
        
        // Calculate initial stats if players data is available
        this.calculateStats();
        
        console.log('✅ RosterStats initialized');
    }

    /**
     * Toggle roster stats visibility
     */
    toggle() {
        console.log('Toggle called, current state:', this.isExpanded);
        
        this.isExpanded = !this.isExpanded;
        
        const content = document.getElementById('rosterStatsContent');
        const expandIcon = document.getElementById('rosterStatsExpandIcon');
        const header = this.container.querySelector('.roster-stats-header');
        
        console.log('Elements found:', {
            content: !!content,
            expandIcon: !!expandIcon,
            header: !!header
        });
        
        if (this.isExpanded) {
            // Expand
            console.log('Expanding...');
            content.style.display = 'block';
            expandIcon.classList.add('expanded');
            header.setAttribute('aria-expanded', 'true');
            
            // Animate in
            content.style.maxHeight = '0';
            content.style.overflow = 'hidden';
            setTimeout(() => {
                content.style.transition = 'max-height 0.3s ease';
                content.style.maxHeight = content.scrollHeight + 'px';
                console.log('Animation complete, scrollHeight:', content.scrollHeight);
            }, 10);
            
            // Calculate fresh stats
            this.calculateStats();
        } else {
            // Collapse
            console.log('Collapsing...');
            content.style.transition = 'max-height 0.3s ease';
            content.style.maxHeight = '0';
            expandIcon.classList.remove('expanded');
            header.setAttribute('aria-expanded', 'false');
            
            setTimeout(() => {
                content.style.display = 'none';
                content.style.maxHeight = '';
                content.style.overflow = '';
            }, 300);
        }
        
        // Save state
        this.saveExpandedState();
    }

    /**
     * Calculate roster statistics from player data
     */
    async calculateStats() {
        // Try to fetch from backend first
        const success = await this.fetchDetailedStats();
        
        if (!success) {
            // Fallback to DOM-based calculation
            this.calculateStatsFromDOM();
        }
    }
    
    /**
     * Calculate stats from DOM (fallback method)
     */
    calculateStatsFromDOM() {
        // Reset stats
        this.statsData = {
            roleGroups: {
                main: 0,
                alt: 0,
                helper: 0
            },
            mains: {
                tokens: { Zenith: 0, Dreadful: 0, Mystic: 0, Venerated: 0 },
                armor: { plate: 0, mail: 0, leather: 0, cloth: 0 }
            },
            all: {
                raidBuffs: {}
            }
        };

        // Get all player items from the DOM
        const playerItems = document.querySelectorAll('.player-item');
        
        playerItems.forEach(playerItem => {
            const characterItems = playerItem.querySelectorAll('.character-item');
            
            characterItems.forEach(charItem => {
                // Get character data from DOM attributes
                const priority = charItem.dataset.priority;
                const isMain = priority === 'main';
                
                // Count role groups
                if (priority === 'main') {
                    this.statsData.roleGroups.main++;
                } else if (priority === 'alt') {
                    this.statsData.roleGroups.alt++;
                } else if (priority === 'helper') {
                    this.statsData.roleGroups.helper++;
                }
                
                // Process character for stats
                this.processCharacterForStats(charItem, isMain);
            });
        });

        // Update the display
        this.updateDisplay();
    }

    /**
     * Process a character for statistics
     * @param {HTMLElement} charItem - Character DOM element
     * @param {boolean} isMain - Whether this is a main character
     */
    processCharacterForStats(charItem, isMain) {
        // This is a simplified version - in reality we'd need the full character data
        // For now, we can only count what's visible in the DOM
        
        // Try to extract class info from the character icon class
        const iconElement = charItem.querySelector('.character-icon');
        if (iconElement) {
            const classList = Array.from(iconElement.classList);
            const classMatch = classList.find(c => c.startsWith('class-'));
            
            if (classMatch && isMain) {
                // Map classes to their tier tokens and armor types
                const classData = this.getClassData(classMatch);
                if (classData) {
                    if (classData.token) {
                        this.statsData.mains.tokens[classData.token]++;
                    }
                    if (classData.armor) {
                        this.statsData.mains.armor[classData.armor]++;
                    }
                }
            }
        }
    }

    /**
     * Get class data mapping
     * @param {string} classString - Class CSS string
     * @returns {Object} Class data with token and armor
     */
    getClassData(classString) {
        const classMap = {
            'class-death_knight': { token: 'Dreadful', armor: 'plate' },
            'class-demon_hunter': { token: 'Venerated', armor: 'leather' },
            'class-druid': { token: 'Venerated', armor: 'leather' },
            'class-evoker': { token: 'Zenith', armor: 'mail' },
            'class-hunter': { token: 'Zenith', armor: 'mail' },
            'class-mage': { token: 'Mystic', armor: 'cloth' },
            'class-monk': { token: 'Venerated', armor: 'leather' },
            'class-paladin': { token: 'Dreadful', armor: 'plate' },
            'class-priest': { token: 'Mystic', armor: 'cloth' },
            'class-rogue': { token: 'Venerated', armor: 'leather' },
            'class-shaman': { token: 'Zenith', armor: 'mail' },
            'class-warlock': { token: 'Mystic', armor: 'cloth' },
            'class-warrior': { token: 'Dreadful', armor: 'plate' }
        };
        
        return classMap[classString] || null;
    }

    /**
     * Update the display with calculated stats
     */
    updateDisplay() {
        // Update role group counts
        document.getElementById('mainsCount').textContent = this.statsData.roleGroups?.main || 0;
        document.getElementById('altsCount').textContent = this.statsData.roleGroups?.alt || 0;
        document.getElementById('helpersCount').textContent = this.statsData.roleGroups?.helper || 0;
        
        // Update token counts
        document.getElementById('mainZenithCount').textContent = this.statsData.mains.tokens.Zenith;
        document.getElementById('mainDreadfulCount').textContent = this.statsData.mains.tokens.Dreadful;
        document.getElementById('mainMysticCount').textContent = this.statsData.mains.tokens.Mystic;
        document.getElementById('mainVeneratedCount').textContent = this.statsData.mains.tokens.Venerated;
        
        // Update armor counts
        document.getElementById('mainPlateCount').textContent = this.statsData.mains.armor.plate;
        document.getElementById('mainMailCount').textContent = this.statsData.mains.armor.mail;
        document.getElementById('mainLeatherCount').textContent = this.statsData.mains.armor.leather;
        document.getElementById('mainClothCount').textContent = this.statsData.mains.armor.cloth;
        
        // Update raid buffs (would need backend data for this)
        this.updateRaidBuffsDisplay();
    }

    /**
     * Update raid buffs display
     */
    updateRaidBuffsDisplay() {
        const buffsList = document.getElementById('raidBuffsList');
        if (!buffsList) return;
        
        // Check if we have raid buff data
        if (this.statsData.all.raidBuffs && Object.keys(this.statsData.all.raidBuffs).length > 0) {
            const buffsHTML = Object.entries(this.statsData.all.raidBuffs)
                .sort(([a], [b]) => a.localeCompare(b)) // Sort alphabetically
                .map(([buffName, count]) => `
                    <div class="buff-item">
                        <span class="buff-name">${buffName}:</span>
                        <span class="buff-count">${count}</span>
                    </div>
                `).join('');
            
            buffsList.innerHTML = buffsHTML;
        } else {
            // Show placeholder if no data
            buffsList.innerHTML = `
                <div class="buff-item placeholder">
                    <span class="buff-name">Loading raid buff data...</span>
                </div>
            `;
        }
    }

    /**
     * Fetch detailed stats from backend
     */
    async fetchDetailedStats() {
        try {
            const response = await fetch('/api/roster-stats');
            if (response.ok) {
                const data = await response.json();
                this.statsData = data;
                this.updateDisplay();
                return true;
            }
            return false;
        } catch (error) {
            console.error('Error fetching roster stats:', error);
            return false;
        }
    }

    /**
     * Save expanded state to localStorage
     */
    saveExpandedState() {
        localStorage.setItem('roster-stats-expanded', this.isExpanded.toString());
    }

    /**
     * Load expanded state from localStorage
     */
    loadExpandedState() {
        const saved = localStorage.getItem('roster-stats-expanded');
        if (saved === 'true') {
            // Don't animate on initial load
            const content = document.getElementById('rosterStatsContent');
            const expandIcon = document.getElementById('rosterStatsExpandIcon');
            const header = this.container.querySelector('.roster-stats-header');
            
            this.isExpanded = true;
            content.style.display = 'block';
            expandIcon.classList.add('expanded');
            header.setAttribute('aria-expanded', 'true');
            
            // Calculate stats
            this.calculateStats();
        }
    }

    /**
     * Refresh stats (public method)
     */
    refresh() {
        if (this.isExpanded) {
            this.calculateStats();
        }
    }
}

// Create global instance
const rosterStats = new RosterStats();

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize immediately
    rosterStats.init();
});

// Also try to initialize if DOM is already loaded
if (document.readyState === 'complete' || document.readyState === 'interactive') {
    setTimeout(() => rosterStats.init(), 0);
}

// Export for global access
window.RosterStats = RosterStats;
window.rosterStats = rosterStats;