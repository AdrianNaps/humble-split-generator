/**
 * PlayerSidebar Component Logic
 * Handles player list and expansion interactions
 * Future React Component: Will become actual React component
 */

class PlayerSidebar {
    constructor() {
        this.expandedPlayers = new Set();
        this.boundClickHandler = this.handleOutsideClick.bind(this);
    }

    /**
     * Initialize the player sidebar
     */
    init() {
        this.addEventListeners();
        console.log('✅ PlayerSidebar initialized');
    }

    /**
     * Add event listeners
     */
    addEventListeners() {
        // Outside click handler to close expanded players
        document.addEventListener('click', this.boundClickHandler);
    }

    /**
     * Toggle player expansion
     * @param {HTMLElement} playerElement - Player item element
     */
    togglePlayer(playerElement) {
        if (!playerElement) return;

        const playerId = playerElement.dataset.playerId;
        const isExpanded = playerElement.classList.contains('expanded');
        
        // Close all other expanded players
        this.closeAllPlayers(playerElement);
        
        // Toggle current player
        if (isExpanded) {
            this.closePlayer(playerElement);
        } else {
            this.expandPlayer(playerElement);
        }
    }

    /**
     * Expand a player
     * @param {HTMLElement} playerElement - Player item element
     */
    expandPlayer(playerElement) {
        if (!playerElement) return;

        const playerId = playerElement.dataset.playerId;
        
        playerElement.classList.add('expanded');
        this.expandedPlayers.add(playerId);

        // Animate character list
        const charactersList = playerElement.querySelector('.characters-list');
        if (charactersList) {
            charactersList.style.maxHeight = charactersList.scrollHeight + 'px';
        }
    }

    /**
     * Close a player
     * @param {HTMLElement} playerElement - Player item element
     */
    closePlayer(playerElement) {
        if (!playerElement) return;

        const playerId = playerElement.dataset.playerId;
        
        playerElement.classList.remove('expanded');
        this.expandedPlayers.delete(playerId);

        // Animate character list
        const charactersList = playerElement.querySelector('.characters-list');
        if (charactersList) {
            charactersList.style.maxHeight = '0';
        }
    }

    /**
     * Close all expanded players except the specified one
     * @param {HTMLElement} exceptElement - Player to keep open
     */
    closeAllPlayers(exceptElement = null) {
        const expandedPlayers = document.querySelectorAll('.player-item.expanded');
        
        expandedPlayers.forEach(playerElement => {
            if (playerElement !== exceptElement) {
                this.closePlayer(playerElement);
            }
        });
    }

    /**
     * Handle clicks outside of player items
     * @param {Event} event - Click event
     */
    handleOutsideClick(event) {
        // Check if click is outside all player items
        if (!event.target.closest('.player-item')) {
            this.closeAllPlayers();
        }
    }

    /**
     * Filter players by search term
     * @param {string} searchTerm - Search term
     */
    filterPlayers(searchTerm) {
        const playerItems = document.querySelectorAll('.player-item');
        const term = searchTerm.toLowerCase().trim();
        
        playerItems.forEach(playerItem => {
            if (!term) {
                // Show all if no search term
                playerItem.style.display = '';
                return;
            }

            // Check player name and discord tag
            const playerName = playerItem.querySelector('.player-name')?.textContent.toLowerCase() || '';
            const discordTag = playerItem.querySelector('.player-discord')?.textContent.toLowerCase() || '';
            
            // Check character names
            const characterNames = Array.from(playerItem.querySelectorAll('.character-name'))
                .map(el => el.textContent.toLowerCase());
            
            const matches = playerName.includes(term) || 
                          discordTag.includes(term) || 
                          characterNames.some(name => name.includes(term));
            
            playerItem.style.display = matches ? '' : 'none';
        });
    }

    /**
     * Get sidebar statistics
     * @returns {Object} Sidebar statistics
     */
    getStats() {
        const playerItems = document.querySelectorAll('.player-item');
        const visiblePlayers = document.querySelectorAll('.player-item:not([style*="display: none"])');
        
        let totalCharacters = 0;
        let visibleCharacters = 0;
        
        playerItems.forEach(playerItem => {
            const characterCount = playerItem.querySelectorAll('.character-item').length;
            totalCharacters += characterCount;
            
            if (!playerItem.style.display || playerItem.style.display !== 'none') {
                visibleCharacters += characterCount;
            }
        });
        
        return {
            totalPlayers: playerItems.length,
            visiblePlayers: visiblePlayers.length,
            totalCharacters,
            visibleCharacters,
            expandedPlayers: this.expandedPlayers.size
        };
    }

    /**
     * Scroll to a specific player
     * @param {string} playerId - Player ID to scroll to
     */
    scrollToPlayer(playerId) {
        const playerElement = document.querySelector(`[data-player-id="${playerId}"]`);
        if (playerElement) {
            smoothScrollTo(playerElement);
            
            // Highlight briefly
            playerElement.style.backgroundColor = 'rgba(13, 110, 253, 0.1)';
            setTimeout(() => {
                playerElement.style.backgroundColor = '';
            }, 2000);
        }
    }

    /**
     * Get expanded player IDs
     * @returns {Array} Array of expanded player IDs
     */
    getExpandedPlayers() {
        return Array.from(this.expandedPlayers);
    }

    /**
     * Restore expanded state (useful for preserving state)
     * @param {Array} playerIds - Array of player IDs to expand
     */
    restoreExpandedState(playerIds) {
        playerIds.forEach(playerId => {
            const playerElement = document.querySelector(`[data-player-id="${playerId}"]`);
            if (playerElement) {
                this.expandPlayer(playerElement);
            }
        });
    }

    /**
     * Clean up event listeners
     */
    destroy() {
        document.removeEventListener('click', this.boundClickHandler);
    }
}

// Create global instance
const playerSidebar = new PlayerSidebar();

// Global function for backward compatibility
function togglePlayer(playerElement) {
    playerSidebar.togglePlayer(playerElement);
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    playerSidebar.init();
});

// Export for global access
window.PlayerSidebar = PlayerSidebar;
window.playerSidebar = playerSidebar;
window.togglePlayer = togglePlayer;