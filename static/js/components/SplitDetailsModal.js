/**
 * SplitDetailsModal Component Logic
 * Handles detailed split analysis and expected value calculations
 */

class SplitDetailsModal {
    constructor() {
        this.modalElement = null;
        this.isOpen = false;
        this.currentGroup = null;
        this.expectedValues = {
            armor: {},
            tier: {}
        };
        this.allRaidBuffs = [];
    }

    /**
     * Initialize the split details modal
     */
    init() {
        this.modalElement = document.getElementById('splitDetailsModal');
        if (!this.modalElement) {
            console.error('Split details modal element not found');
            return;
        }

        // Add event listeners
        this.addEventListeners();
        
        // Fetch raid buffs list
        this.fetchRaidBuffsList();
        
        console.log('✅ SplitDetailsModal initialized');
    }

    /**
     * Add event listeners
     */
    addEventListeners() {
        // Close on overlay click
        this.modalElement.addEventListener('click', (e) => {
            if (e.target === this.modalElement) {
                this.close();
            }
        });

        // Close on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.close();
            }
        });
    }

    /**
     * Calculate expected values based on mains distribution and number of groups
     * @param {Object} mainsData - Data about mains (armor and tier counts)
     * @param {number} numGroups - Number of split groups
     */
    calculateExpectedValues(mainsData, numGroups) {
        // Calculate expected armor distribution
        if (mainsData.armor) {
            Object.entries(mainsData.armor).forEach(([type, count]) => {
                this.expectedValues.armor[type] = (count / numGroups).toFixed(2);
            });
        }

        // Calculate expected tier distribution
        if (mainsData.tier) {
            Object.entries(mainsData.tier).forEach(([type, count]) => {
                this.expectedValues.tier[type] = (count / numGroups).toFixed(2);
            });
        }
    }

    /**
     * Open modal with group details
     * @param {Object} group - Group data
     * @param {number} groupId - Group ID
     * @param {number} totalGroups - Total number of groups
     */
    async open(group, groupId, totalGroups) {
        if (!group) return;

        this.currentGroup = group;
        this.isOpen = true;

        // Update title
        document.getElementById('splitDetailsTitle').textContent = `Group ${groupId} Details`;

        // Fetch expected values from roster stats
        await this.fetchExpectedValues(totalGroups);

        // Update all sections
        this.updateComposition(group);
        this.updateArmorDistribution(group);
        this.updateTierDistribution(group);
        this.updateRaidBuffs(group);

        // Show modal
        this.modalElement.classList.add('active');
    }

    /**
     * Close the modal
     */
    close() {
        this.isOpen = false;
        this.modalElement.classList.remove('active');
        this.currentGroup = null;
    }

    /**
     * Fetch expected values from roster stats
     * @param {number} numGroups - Number of groups
     */
    async fetchExpectedValues(numGroups) {
        try {
            const response = await fetch('/api/roster-stats');
            if (response.ok) {
                const data = await response.json();
                
                // Calculate expected values from mains data
                this.calculateExpectedValues({
                    armor: data.mains.armor,
                    tier: data.mains.tokens
                }, numGroups);
            }
        } catch (error) {
            console.error('Error fetching expected values:', error);
        }
    }

    /**
     * Fetch list of all raid buffs
     */
    async fetchRaidBuffsList() {
        try {
            const response = await fetch('/api/roster-stats');
            if (response.ok) {
                const data = await response.json();
                if (data.all && data.all.raidBuffs) {
                    this.allRaidBuffs = Object.keys(data.all.raidBuffs).sort();
                }
            }
        } catch (error) {
            console.error('Error fetching raid buffs list:', error);
        }
    }

    /**
     * Update composition section
     * @param {Object} group - Group data
     */
    updateComposition(group) {
        const compositionEl = document.getElementById('compositionDetails');
        
        // Count mains by role
        let tankMains = 0, healerMains = 0, dpsMains = 0, totalMains = 0;
        
        group.characters.forEach(char => {
            if (char.role_group === 'main') {
                totalMains++;
                if (char.role_raid === 'tank') tankMains++;
                else if (char.role_raid === 'healer') healerMains++;
                else dpsMains++;
            }
        });

        const dps = group.dps || 0;
        const tanks = group.tanks || 0;
        const healers = group.healers || 0;

        compositionEl.innerHTML = `
            <div class="composition-line">
                <strong>${tanks}</strong> Tanks <span class="mains-count">(${tankMains} ${tankMains === 1 ? 'Main' : 'Mains'})</span> / 
                <strong>${healers}</strong> Healers <span class="mains-count">(${healerMains} ${healerMains === 1 ? 'Main' : 'Mains'})</span> / 
                <strong>${dps}</strong> DPS <span class="mains-count">(${dpsMains} ${dpsMains === 1 ? 'Main' : 'Mains'})</span>
            </div>
            <div class="composition-line">
                <strong>Main Characters:</strong> ${totalMains}
            </div>
        `;
    }

    /**
     * Update armor distribution section
     * @param {Object} group - Group data
     */
    updateArmorDistribution(group) {
        const armorEl = document.getElementById('armorDetails');
        const armorDist = group.armor_distribution_mains || {};
        
        const armorTypes = ['plate', 'mail', 'leather', 'cloth'];
        const armorHTML = armorTypes.map(type => {
            const actual = armorDist[type] || 0;
            const expected = parseFloat(this.expectedValues.armor[type] || 0);
            const isGood = actual >= Math.floor(expected);
            const statusClass = isGood ? 'good' : 'warning';
            
            // Capitalize first letter
            const displayType = type.charAt(0).toUpperCase() + type.slice(1);
            
            return `
                <div class="distribution-item ${statusClass}">
                    <span class="dist-label">${displayType}:</span>
                    <span class="dist-value">
                        <strong>${actual}</strong> out of ${expected}
                    </span>
                </div>
            `;
        }).join('');
        
        armorEl.innerHTML = armorHTML;
    }

    /**
     * Update tier distribution section
     * @param {Object} group - Group data
     */
    updateTierDistribution(group) {
        const tierEl = document.getElementById('tierDetails');
        const tierDist = group.tier_distribution_mains || {};
        
        const tierTypes = ['Zenith', 'Dreadful', 'Mystic', 'Venerated'];
        const tierHTML = tierTypes.map(type => {
            const actual = tierDist[type] || 0;
            const expected = parseFloat(this.expectedValues.tier[type] || 0);
            const isGood = actual >= Math.floor(expected);
            const statusClass = isGood ? 'good' : 'warning';
            
            return `
                <div class="distribution-item ${statusClass}">
                    <span class="dist-label">${type}:</span>
                    <span class="dist-value">
                        <strong>${actual}</strong> out of ${expected}
                    </span>
                </div>
            `;
        }).join('');
        
        tierEl.innerHTML = tierHTML;
    }

    /**
     * Update raid buffs section
     * @param {Object} group - Group data
     */
    updateRaidBuffs(group) {
        const buffsEl = document.getElementById('raidBuffsDetails');
        
        // Get buffs provided by this group's characters
        const groupBuffs = new Set();
        group.characters.forEach(char => {
            if (char.buffs && Array.isArray(char.buffs)) {
                char.buffs.forEach(buff => groupBuffs.add(buff));
            }
        });

        // Create buff display
        const buffsHTML = this.allRaidBuffs.map(buffName => {
            // This is simplified - in reality, we'd need to map buff names to buff IDs
            const hasBuff = groupBuffs.has(buffName) || 
                           group.characters.some(char => 
                               char.buffs && char.buffs.some(b => b.includes(buffName.toLowerCase().replace(/\s+/g, '_')))
                           );
            
            const statusClass = hasBuff ? 'has-buff' : 'missing-buff';
            const icon = hasBuff ? '✓' : '✗';
            
            return `
                <div class="buff-item ${statusClass}">
                    <span class="buff-icon">${icon}</span>
                    <span class="buff-name">${buffName}</span>
                </div>
            `;
        }).join('');
        
        buffsEl.innerHTML = buffsHTML || '<div class="no-buffs">No raid buff data available</div>';
    }

    /**
     * Get detailed group data with buff mappings
     * @param {Object} group - Group data
     * @returns {Object} Enhanced group data
     */
    async getDetailedGroupData(group) {
        // In a real implementation, this would fetch additional data about buffs
        // For now, we'll work with what we have
        return group;
    }
}

// Create global instance
const splitDetailsModal = new SplitDetailsModal();

// Global functions
function openSplitDetailsModal(group, groupId, totalGroups) {
    splitDetailsModal.open(group, groupId, totalGroups);
}

function closeSplitDetailsModal() {
    splitDetailsModal.close();
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    splitDetailsModal.init();
});

// Export for global access
window.SplitDetailsModal = SplitDetailsModal;
window.splitDetailsModal = splitDetailsModal;
window.openSplitDetailsModal = openSplitDetailsModal;
window.closeSplitDetailsModal = closeSplitDetailsModal;