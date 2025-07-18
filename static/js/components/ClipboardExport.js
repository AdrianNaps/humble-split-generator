/**
 * ClipboardExport.js
 * Adds functionality to export raid groups to clipboard for spreadsheet pasting
 */

class ClipboardExport {
    constructor() {
        // WoW class colors in hex for spreadsheet formatting
        this.classColors = {
            'Death Knight': '#C41F3B',
            'Demon Hunter': '#A330C9',
            'Druid': '#FF7D0A',
            'Evoker': '#33937F',
            'Hunter': '#ABD473',
            'Mage': '#69CCF0',
            'Monk': '#00FF96',
            'Paladin': '#F58CBA',
            'Priest': '#FFFFFF',
            'Rogue': '#FFF569',
            'Shaman': '#0070DE',
            'Warlock': '#9482C9',
            'Warrior': '#C79C6E'
        };
    }

    /**
     * Export groups to clipboard in various formats
     * @param {Array} groups - Array of group objects from RaidGroups
     * @param {string} format - Export format ('csv', 'html')
     */
    async exportToClipboard(groups, format = 'html') {
        if (!groups || groups.length === 0) {
            showErrorMessage('No groups to export');
            return false;
        }

        try {
            let clipboardData;
            
            switch (format) {
                case 'csv':
                    clipboardData = this.generateCSV(groups);
                    break;
                case 'html':
                default:
                    clipboardData = this.generateHTMLTable(groups);
                    break;
            }

            // Copy to clipboard
            const success = await this.copyToClipboard(clipboardData, format);
            
            if (success) {
                showSuccessMessage(`Groups copied to clipboard! Paste into your spreadsheet.`);
                return true;
            } else {
                showErrorMessage('Failed to copy to clipboard');
                return false;
            }
            
        } catch (error) {
            console.error('Export error:', error);
            showErrorMessage('Error exporting groups: ' + error.message);
            return false;
        }
    }



    /**
     * Generate CSV format for two-column layout
     * @param {Array} groups - Array of group objects
     * @returns {string} CSV formatted string
     */
    generateCSV(groups) {
        const rows = [];
        
        // Header row - each split takes 2 columns with empty columns between
        const headers = [];
        groups.forEach((g, index) => {
            if (index > 0) {
                headers.push(''); // Empty column for buffer
            }
            headers.push(`"Split ${g.group_id}"`);
            headers.push(''); // Empty header for second column
        });
        rows.push(headers.join(','));
        
        // Calculate rows needed for two-column layout
        const charactersPerColumn = groups.map(g => Math.ceil(g.characters.length / 2));
        const maxRows = Math.max(...charactersPerColumn);
        
        // Character rows - two columns per split with buffer columns
        for (let row = 0; row < maxRows; row++) {
            const rowData = [];
            
            groups.forEach((group, groupIndex) => {
                // Add empty buffer column before each split (except the first)
                if (groupIndex > 0) {
                    rowData.push('""');
                }
                
                const halfLength = Math.ceil(group.characters.length / 2);
                
                // First column of this split
                const firstColIndex = row;
                if (firstColIndex < halfLength) {
                    const char = group.characters[firstColIndex];
                    rowData.push(`"${char.name.replace(/"/g, '""')}"`);
                } else {
                    rowData.push('""');
                }
                
                // Second column of this split
                const secondColIndex = row + halfLength;
                if (secondColIndex < group.characters.length) {
                    const char = group.characters[secondColIndex];
                    rowData.push(`"${char.name.replace(/"/g, '""')}"`);
                } else {
                    rowData.push('""');
                }
            });
            
            rows.push(rowData.join(','));
        }
        
        return rows.join('\n');
    }

    /**
     * Generate HTML table with inline styles for rich formatting
     * @param {Array} groups - Array of group objects
     * @returns {string} HTML table string
     */
    generateHTMLTable(groups) {
        let html = '<table style="border-collapse: collapse; font-family: Arial, sans-serif;">';
        
        // Header row - each split takes 2 columns with empty columns between
        html += '<tr>';
        groups.forEach((group, index) => {
            // Add empty column before each split (except the first)
            if (index > 0) {
                html += '<td style="border: none; padding: 0; width: 20px;"></td>';
            }
            html += `<th colspan="2" style="background-color: #333; color: white; padding: 8px; border: 1px solid #000; font-weight: bold; text-align: center;">Split ${group.group_id}</th>`;
        });
        html += '</tr>';
        
        // Calculate rows needed for two-column layout
        const charactersPerColumn = groups.map(g => Math.ceil(g.characters.length / 2));
        const maxRows = Math.max(...charactersPerColumn);
        
        // Character rows - two columns per split with buffer columns
        for (let row = 0; row < maxRows; row++) {
            html += '<tr>';
            
            groups.forEach((group, groupIndex) => {
                // Add empty buffer column before each split (except the first)
                if (groupIndex > 0) {
                    html += '<td style="border: none; padding: 0; width: 20px;"></td>';
                }
                
                const halfLength = Math.ceil(group.characters.length / 2);
                
                // First column of this split
                const firstColIndex = row;
                if (firstColIndex < halfLength) {
                    const char = group.characters[firstColIndex];
                    const bgColor = this.classColors[char.class_name] || '#808080';
                    
                    html += `<td style="background-color: ${bgColor}; color: black; padding: 6px; border: 1px solid #666; text-align: center; font-weight: 600; min-width: 80px;">${char.name}</td>`;
                } else {
                    html += '<td style="padding: 6px; border: 1px solid #666; min-width: 80px;"></td>';
                }
                
                // Second column of this split
                const secondColIndex = row + halfLength;
                if (secondColIndex < group.characters.length) {
                    const char = group.characters[secondColIndex];
                    const bgColor = this.classColors[char.class_name] || '#808080';
                    
                    html += `<td style="background-color: ${bgColor}; color: black; padding: 6px; border: 1px solid #666; text-align: center; font-weight: 600; min-width: 80px;">${char.name}</td>`;
                } else {
                    html += '<td style="padding: 6px; border: 1px solid #666; min-width: 80px;"></td>';
                }
            });
            
            html += '</tr>';
        }
        
        // Add group statistics rows
        const statRows = [
            {
                label: 'Composition:',
                getValue: (g) => `${g.tanks || 0}T / ${g.healers || 0}H / ${g.dps || 0}D`
            },
            {
                label: 'Main Characters:',
                getValue: (g) => g.mains_count || 0
            },
            {
                label: 'Raid Buffs:',
                getValue: (g) => `${g.raid_buff_count || 0}/${g.total_raid_buffs || 11}`
            },
            {
                label: 'Armor (Mains):',
                getValue: (g) => {
                    const armor = g.armor_distribution_mains || {};
                    return `${armor.plate || 0}P / ${armor.mail || 0}M / ${armor.leather || 0}L / ${armor.cloth || 0}C`;
                }
            },
            {
                label: 'Tier (Mains):',
                getValue: (g) => {
                    const tier = g.tier_distribution_mains || {};
                    return `${tier.Zenith || 0}Z / ${tier.Dreadful || 0}D / ${tier.Mystic || 0}M / ${tier.Venerated || 0}V`;
                }
            }
        ];
        
        // Add each stat row
        statRows.forEach(stat => {
            html += '<tr>';
            
            groups.forEach((group, groupIndex) => {
                // Add empty buffer column before each split (except the first)
                if (groupIndex > 0) {
                    html += '<td style="border: none; padding: 0; width: 20px;"></td>';
                }
                
                // Stat label cell
                html += `<td style="background-color: #f0f0f0; color: black; padding: 6px; border: 1px solid #666; text-align: right; font-weight: bold; font-size: 12px;">${stat.label}</td>`;
                
                // Stat value cell
                html += `<td style="background-color: #f0f0f0; color: black; padding: 6px; border: 1px solid #666; text-align: left; font-size: 12px;">${stat.getValue(group)}</td>`;
            });
            
            html += '</tr>';
        });
        
        html += '</table>';
        return html;
    }

    /**
     * Advanced copy to clipboard with multiple formats
     * @param {string} data - Data to copy
     * @param {string} format - Format type
     * @returns {Promise<boolean>} Success status
     */
    async copyToClipboard(data, format) {
        try {
            if (format === 'html' && navigator.clipboard.write) {
                // For HTML, we can provide both plain text and HTML versions
                const textData = this.htmlTableToPlainText(data);
                
                const htmlBlob = new Blob([data], { type: 'text/html' });
                const textBlob = new Blob([textData], { type: 'text/plain' });
                
                const clipboardItem = new ClipboardItem({
                    'text/html': htmlBlob,
                    'text/plain': textBlob
                });
                
                await navigator.clipboard.write([clipboardItem]);
                return true;
            } else {
                // Fallback to plain text copy
                await navigator.clipboard.writeText(data);
                return true;
            }
        } catch (error) {
            console.error('Clipboard error:', error);
            
            // Fallback method
            const textArea = document.createElement('textarea');
            textArea.value = data;
            textArea.style.position = 'fixed';
            textArea.style.left = '-999999px';
            document.body.appendChild(textArea);
            textArea.select();
            
            try {
                document.execCommand('copy');
                document.body.removeChild(textArea);
                return true;
            } catch (e) {
                document.body.removeChild(textArea);
                return false;
            }
        }
    }

    /**
     * Convert HTML table to plain text CSV
     * @param {string} html - HTML table string
     * @returns {string} Plain text version
     */
    htmlTableToPlainText(html) {
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = html;
        
        const rows = [];
        const trs = tempDiv.querySelectorAll('tr');
        
        trs.forEach(tr => {
            const cells = [];
            const tds = tr.querySelectorAll('th, td');
            tds.forEach(td => {
                // Escape quotes for CSV
                const text = td.textContent.replace(/"/g, '""');
                cells.push(`"${text}"`);
            });
            rows.push(cells.join(','));
        });
        
        return rows.join('\n');
    }



    /**
     * Create export button UI
     * @returns {HTMLElement} Export button element
     */
    createExportButton() {
        const button = document.createElement('button');
        button.className = 'action-btn export-btn';
        button.innerHTML = '<i class="fas fa-clipboard"></i> Copy to Spreadsheet';
        button.style.cssText = `
            background-color: #28a745;
            margin-left: 8px;
        `;
        
        button.addEventListener('click', async () => {
            const groups = window.raidGroups?.getCurrentGroups();
            if (groups && groups.length > 0) {
                // Show format selection dialog
                const format = await this.showFormatDialog();
                if (format) {
                    await this.exportToClipboard(groups, format);
                }
            } else {
                showErrorMessage('No groups available to export');
            }
        });
        
        return button;
    }

    /**
     * Show format selection dialog
     * @returns {Promise<string|null>} Selected format or null
     */
    async showFormatDialog() {
        return new Promise(resolve => {
            // Create a simple modal for format selection
            const modal = document.createElement('div');
            modal.className = 'modal-overlay active';
            modal.style.zIndex = '2000';
            
            const container = document.createElement('div');
            container.className = 'modal-container';
            container.style.maxWidth = '400px';
            
            container.innerHTML = `
                <div class="modal-header">
                    <h3 class="modal-title">Export Format</h3>
                </div>
                <div class="modal-body">
                    <p style="margin-bottom: 16px;">Choose export format for your spreadsheet:</p>
                    <div style="display: flex; flex-direction: column; gap: 12px;">
                        <button class="btn btn-primary" data-format="html" style="width: 100%;">
                            <i class="fas fa-palette"></i> HTML Table (With Colors)
                        </button>
                        <button class="btn btn-primary" data-format="csv" style="width: 100%;">
                            <i class="fas fa-file-csv"></i> CSV Format
                        </button>
                    </div>
                    <p style="margin-top: 16px; font-size: 14px; color: #666;">
                        <strong>Tip:</strong> Use "HTML Table" for best visual formatting with class colors.
                    </p>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" data-format="cancel">Cancel</button>
                </div>
            `;
            
            modal.appendChild(container);
            document.body.appendChild(modal);
            
            // Add click handlers
            container.addEventListener('click', (e) => {
                const button = e.target.closest('button[data-format]');
                if (button) {
                    const format = button.dataset.format;
                    document.body.removeChild(modal);
                    resolve(format === 'cancel' ? null : format);
                }
            });
            
            // Close on outside click
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    document.body.removeChild(modal);
                    resolve(null);
                }
            });
        });
    }

    /**
     * Generate class color reference sheet
     * @returns {string} TSV formatted color reference
     */
    generateColorReference() {
        const rows = ['Class\tColor Code'];
        
        Object.entries(this.classColors).forEach(([className, color]) => {
            rows.push(`${className}\t${color}`);
        });
        
        return rows.join('\n');
    }
}

// Create global instance
const clipboardExport = new ClipboardExport();

// Add export button to the UI when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Wait for initial load
    setTimeout(() => {
        const headerActions = document.querySelector('.header-actions');
        if (headerActions) {
            const exportButton = clipboardExport.createExportButton();
            headerActions.appendChild(exportButton);
            console.log('✅ Export button added to UI');
        }
    }, 500);
});

// Global function for easy access
async function exportGroupsToClipboard(format = 'html') {
    const groups = window.raidGroups?.getCurrentGroups();
    if (groups && groups.length > 0) {
        return await clipboardExport.exportToClipboard(groups, format);
    } else {
        showErrorMessage('No groups available to export');
        return false;
    }
}

// Export for global access
window.ClipboardExport = ClipboardExport;
window.clipboardExport = clipboardExport;
window.exportGroupsToClipboard = exportGroupsToClipboard;