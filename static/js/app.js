/**
 * Main App Initialization
 * Coordinates all components and handles global app state
 * Future React: Will become App.js with component composition
 */

class WoWRosterApp {
    constructor() {
        this.components = {};
        this.initialized = false;
        this.appState = {
            currentPage: 'dashboard',
            lastActivity: Date.now(),
            settings: null,
            generationState: null
        };
    }

    /**
     * Initialize the entire application
     */
    async init() {
        if (this.initialized) {
            console.warn('App already initialized');
            return;
        }

        console.log('🚀 Initializing WoW Roster Manager...');

        try {
            // Initialize core systems
            await this.initializeComponents();
            this.setupGlobalEventListeners();
            this.startAppStateTracking();
            
            this.initialized = true;
            console.log('✅ WoW Roster Manager initialized successfully');
            
            // Show welcome message
            this.showWelcomeMessage();
            
        } catch (error) {
            console.error('❌ Failed to initialize app:', error);
            showErrorMessage('Failed to initialize application: ' + error.message);
        }
    }

    /**
     * Initialize all components
     */
    async initializeComponents() {
        // Initialize hooks (state management)
        this.components.settings = useRaidSettings();
        this.components.generation = useRaidGeneration();
        
        // Components are already initialized via their own files
        // This just tracks references
        this.components.settingsModal = window.settingsModal;
        this.components.raidGroups = window.raidGroups;
        this.components.playerSidebar = window.playerSidebar;
        
        console.log('✅ All components initialized');
    }

    /**
     * Setup global event listeners
     */
    setupGlobalEventListeners() {
        // Track user activity
        ['click', 'keydown', 'scroll'].forEach(eventType => {
            document.addEventListener(eventType, () => {
                this.appState.lastActivity = Date.now();
            }, { passive: true });
        });

        // Handle visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                console.log('App went to background');
            } else {
                console.log('App came to foreground');
                this.checkForUpdates();
            }
        });

        // Handle window resize
        window.addEventListener('resize', debounce(() => {
            this.handleWindowResize();
        }, 250));

        // Handle beforeunload (page refresh/close)
        window.addEventListener('beforeunload', (e) => {
            this.handleBeforeUnload(e);
        });

        console.log('✅ Global event listeners setup');
    }

    /**
     * Start tracking application state
     */
    startAppStateTracking() {
        // Subscribe to settings changes
        this.components.settings.subscribe((settings) => {
            this.appState.settings = settings;
            this.saveAppState();
        });

        // Subscribe to generation changes
        this.components.generation.subscribe((state) => {
            this.appState.generationState = state;
            this.saveAppState();
        });

        // Load saved state
        this.loadAppState();

        console.log('✅ App state tracking started');
    }

    /**
     * Show welcome message on first load
     */
    showWelcomeMessage() {
        const hasSeenWelcome = localStorage.getItem('wow-roster-welcome-seen');
        if (!hasSeenWelcome) {
            setTimeout(() => {
                showInfoMessage('Welcome to WoW Roster Manager! Click "Generate Splits" to get started.', 5000);
                localStorage.setItem('wow-roster-welcome-seen', 'true');
            }, 1000);
        }
    }

    /**
     * Handle window resize
     */
    handleWindowResize() {
        // Adjust layout for mobile if needed
        const isMobile = window.innerWidth <= 768;
        document.body.classList.toggle('mobile-layout', isMobile);
    }

    /**
     * Check for updates when app comes back to foreground
     */
    async checkForUpdates() {
        try {
            // Check if backend data has changed
            const response = await fetch('/api/stats');
            if (response.ok) {
                const stats = await response.json();
                // Could compare with cached stats to detect changes
                console.log('Backend status check:', stats);
            }
        } catch (error) {
            console.warn('Could not check for updates:', error);
        }
    }

    /**
     * Handle page unload
     * @param {BeforeUnloadEvent} e - Unload event
     */
    handleBeforeUnload(e) {
        // Save current state
        this.saveAppState();
        
        // Only show warning if there are unsaved changes
        const hasUnsavedChanges = this.hasUnsavedChanges();
        if (hasUnsavedChanges) {
            e.preventDefault();
            e.returnValue = '';
        }
    }

    /**
     * Check if there are unsaved changes
     * @returns {boolean}
     */
    hasUnsavedChanges() {
        // Check if settings modal is open with changes
        if (this.components.settingsModal?.isModalOpen()) {
            const formSettings = getSettingsFromForm();
            const currentSettings = this.components.settings.settings;
            
            return JSON.stringify(formSettings) !== JSON.stringify(currentSettings);
        }
        
        return false;
    }

    /**
     * Save application state to localStorage
     */
    saveAppState() {
        try {
            const stateToSave = {
                settings: this.appState.settings,
                lastActivity: this.appState.lastActivity,
                expandedPlayers: this.components.playerSidebar?.getExpandedPlayers() || [],
                timestamp: Date.now()
            };
            
            localStorage.setItem('wow-roster-app-state', JSON.stringify(stateToSave));
        } catch (error) {
            console.warn('Could not save app state:', error);
        }
    }

    /**
     * Load application state from localStorage
     */
    loadAppState() {
        try {
            const savedState = localStorage.getItem('wow-roster-app-state');
            if (savedState) {
                const state = JSON.parse(savedState);
                
                // Restore settings if they exist
                if (state.settings) {
                    updateSettings(state.settings);
                }
                
                // Restore expanded players after a short delay
                if (state.expandedPlayers && state.expandedPlayers.length > 0) {
                    setTimeout(() => {
                        this.components.playerSidebar?.restoreExpandedState(state.expandedPlayers);
                    }, 500);
                }
                
                console.log('✅ App state restored from localStorage');
            }
        } catch (error) {
            console.warn('Could not load app state:', error);
        }
    }

    /**
     * Clear all saved state
     */
    clearSavedState() {
        localStorage.removeItem('wow-roster-app-state');
        localStorage.removeItem('wow-roster-welcome-seen');
        console.log('✅ Saved state cleared');
    }

    /**
     * Get current application statistics
     * @returns {Object} App statistics
     */
    getAppStats() {
        const sidebarStats = this.components.playerSidebar?.getStats() || {};
        const generationStats = getGroupStatistics() || {};
        
        return {
            initialized: this.initialized,
            currentPage: this.appState.currentPage,
            uptime: Date.now() - this.appState.lastActivity,
            components: Object.keys(this.components).length,
            sidebar: sidebarStats,
            generation: generationStats,
            memoryUsage: this.getMemoryUsage()
        };
    }

    /**
     * Get memory usage information
     * @returns {Object} Memory usage stats
     */
    getMemoryUsage() {
        if (performance.memory) {
            return {
                used: Math.round(performance.memory.usedJSHeapSize / 1024 / 1024),
                total: Math.round(performance.memory.totalJSHeapSize / 1024 / 1024),
                limit: Math.round(performance.memory.jsHeapSizeLimit / 1024 / 1024)
            };
        }
        return null;
    }

    /**
     * Export current roster data
     * @returns {Object} Exportable data
     */
    async exportData() {
        try {
            const response = await fetch('/api/players');
            const playerData = await response.json();
            
            const exportData = {
                timestamp: new Date().toISOString(),
                version: '1.0',
                settings: this.appState.settings,
                players: playerData.players,
                totalCharacters: playerData.total_characters,
                generatedGroups: this.appState.generationState?.currentGroups || []
            };
            
            return exportData;
        } catch (error) {
            console.error('Error exporting data:', error);
            throw error;
        }
    }

    /**
     * Download data as JSON file
     */
    async downloadData() {
        try {
            const data = await this.exportData();
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            
            const link = document.createElement('a');
            link.href = url;
            link.download = `wow-roster-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            URL.revokeObjectURL(url);
            showSuccessMessage('Roster data downloaded successfully!');
        } catch (error) {
            showErrorMessage('Failed to download data: ' + error.message);
        }
    }

    /**
     * Handle errors globally
     * @param {Error} error - Error to handle
     * @param {string} context - Context where error occurred
     */
    handleError(error, context = 'Unknown') {
        console.error(`Error in ${context}:`, error);
        
        // Show user-friendly message
        showErrorMessage(`An error occurred in ${context}. Please try again.`);
        
        // Could send to error reporting service here
    }

    /**
     * Cleanup and destroy the app
     */
    destroy() {
        // Save final state
        this.saveAppState();
        
        // Cleanup components
        Object.values(this.components).forEach(component => {
            if (component.destroy) {
                component.destroy();
            }
        });
        
        this.initialized = false;
        console.log('✅ App destroyed');
    }
}

// Create global app instance
const app = new WoWRosterApp();

// Global functions for console access and debugging
function getAppStats() {
    return app.getAppStats();
}

function exportRosterData() {
    return app.exportData();
}

function downloadRosterData() {
    return app.downloadData();
}

function clearAppData() {
    app.clearSavedState();
    showInfoMessage('App data cleared. Refresh to start fresh.');
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    app.init();
});

// Global error handler
window.addEventListener('error', function(e) {
    app.handleError(e.error, 'Global');
});

// Handle unhandled promise rejections
window.addEventListener('unhandledrejection', function(e) {
    app.handleError(e.reason, 'Promise');
    e.preventDefault();
});

// Export for global access
window.WoWRosterApp = WoWRosterApp;
window.app = app;
window.getAppStats = getAppStats;
window.exportRosterData = exportRosterData;
window.downloadRosterData = downloadRosterData;
window.clearAppData = clearAppData;

// Development helpers (only in development)
if (window.location.hostname === 'localhost') {
    window.dev = {
        app,
        getStats: getAppStats,
        clearData: clearAppData,
        components: () => app.components,
        state: () => app.appState
    };
}