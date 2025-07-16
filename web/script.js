// Global variables
let allLeads = [];
let filteredLeads = [];
let summaryData = {};

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    hideLoadingOverlay();
    loadData();
    setupEventListeners();
});

// Load data from JSON files
async function loadData() {
    try {
        showLoadingOverlay();
        
        // Load all data files
        const [leadsResponse, summaryResponse] = await Promise.all([
            fetch('data/hot_leads.json'),
            fetch('data/summary.json')
        ]);

        allLeads = await leadsResponse.json();
        summaryData = await summaryResponse.json();
        
        // Initialize the UI
        updateDashboardStats();
        filteredLeads = [...allLeads];
        renderLeadsTable();
        updateLastUpdated();
        
        hideLoadingOverlay();
    } catch (error) {
        console.error('Error loading data:', error);
        showError('Failed to load data. Please refresh the page.');
        hideLoadingOverlay();
    }
}

// Update dashboard statistics
function updateDashboardStats() {
    document.getElementById('total-leads').textContent = summaryData.total_leads?.toLocaleString() || '0';
    document.getElementById('hot-leads').textContent = summaryData.hot_leads?.toLocaleString() || '0';
    document.getElementById('podiatrist-groups').textContent = summaryData.podiatrist_groups?.toLocaleString() || '0';
    document.getElementById('wound-care-groups').textContent = summaryData.wound_care_groups?.toLocaleString() || '0';
}

// Update last updated timestamp
function updateLastUpdated() {
    if (summaryData.last_updated) {
        const date = new Date(summaryData.last_updated);
        document.getElementById('last-updated').textContent = date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    }
}

// Setup event listeners
function setupEventListeners() {
    // Filter event listeners
    document.getElementById('priority-filter').addEventListener('change', applyFilters);
    document.getElementById('category-filter').addEventListener('change', applyFilters);
    document.getElementById('search-filter').addEventListener('input', debounce(applyFilters, 300));
}

// Debounce function for search input
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Apply filters to the leads
function applyFilters() {
    const priorityFilter = document.getElementById('priority-filter').value;
    const categoryFilter = document.getElementById('category-filter').value;
    const searchFilter = document.getElementById('search-filter').value.toLowerCase();

    filteredLeads = allLeads.filter(lead => {
        // Priority filter
        if (priorityFilter && lead.priority !== priorityFilter) {
            return false;
        }

        // Category filter
        if (categoryFilter && lead.category !== categoryFilter) {
            return false;
        }

        // Search filter
        if (searchFilter) {
            const searchableText = [
                lead.specialties,
                lead.address,
                lead.zip,
                lead.category,
                lead.phone
            ].join(' ').toLowerCase();
            
            if (!searchableText.includes(searchFilter)) {
                return false;
            }
        }

        return true;
    });

    renderLeadsTable();
}

// Reset all filters
function resetFilters() {
    document.getElementById('priority-filter').value = '';
    document.getElementById('category-filter').value = '';
    document.getElementById('search-filter').value = '';
    
    filteredLeads = [...allLeads];
    renderLeadsTable();
}

// Render the leads table
function renderLeadsTable() {
    const tbody = document.getElementById('leads-tbody');
    
    if (filteredLeads.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" class="loading">No leads match your filters.</td></tr>';
        return;
    }

    tbody.innerHTML = filteredLeads.map(lead => `
        <tr>
            <td>
                <div class="score-badge ${getScoreClass(lead.score)}">
                    ${lead.score}
                </div>
            </td>
            <td>
                <span class="priority-badge ${getPriorityClass(lead.priority)}">
                    ${lead.priority}
                </span>
            </td>
            <td>${lead.category}</td>
            <td>
                <strong>${lead.providers}</strong> provider${lead.providers > 1 ? 's' : ''}
            </td>
            <td>
                ${lead.phone ? `<a href="tel:${lead.phone}" class="btn-call"><i class="fas fa-phone"></i> ${lead.phone}</a>` : 'N/A'}
            </td>
            <td>
                <div class="address-cell">
                    ${lead.address || 'Address not available'}
                </div>
            </td>
            <td><strong>${lead.zip}</strong></td>
            <td>
                ${lead.population ? lead.population.toLocaleString() : 'N/A'}
            </td>
            <td>
                <div class="specialties-cell">
                    ${formatSpecialties(lead.specialties)}
                </div>
            </td>
            <td>
                <div class="action-buttons">
                    ${lead.phone ? `<a href="tel:${lead.phone}" class="btn-call"><i class="fas fa-phone"></i></a>` : ''}
                    <button class="btn-email" onclick="copyLeadInfo(${lead.id})">
                        <i class="fas fa-copy"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

// Get CSS class for score badge
function getScoreClass(score) {
    if (score >= 80) return 'score-high';
    if (score >= 60) return 'score-medium';
    return 'score-low';
}

// Get CSS class for priority badge
function getPriorityClass(priority) {
    if (priority === 'A+ Priority') return 'priority-a-plus';
    if (priority === 'A Priority') return 'priority-a';
    return 'priority-b';
}

// Format specialties for display
function formatSpecialties(specialties) {
    if (!specialties) return 'N/A';
    
    // Split by comma and create badges for each specialty
    const specialtyList = specialties.split(',').map(s => s.trim());
    
    // Highlight key specialties
    return specialtyList.map(specialty => {
        let className = 'specialty-tag';
        if (specialty.toLowerCase().includes('podiatrist')) {
            className += ' specialty-podiatrist';
        } else if (specialty.toLowerCase().includes('wound care')) {
            className += ' specialty-wound-care';
        } else if (specialty.toLowerCase().includes('mohs')) {
            className += ' specialty-mohs';
        }
        
        return `<span class="${className}">${specialty}</span>`;
    }).join(' ');
}

// Copy lead information to clipboard
function copyLeadInfo(leadId) {
    const lead = allLeads.find(l => l.id === leadId);
    if (!lead) return;

    const leadInfo = `
LEAD INFORMATION
================
Priority: ${lead.priority}
Category: ${lead.category}
Providers: ${lead.providers}
Phone: ${lead.phone}
Address: ${lead.address}
ZIP: ${lead.zip}
Population: ${lead.population?.toLocaleString() || 'N/A'}
Specialties: ${lead.specialties}
Score: ${lead.score}/100
    `.trim();

    navigator.clipboard.writeText(leadInfo).then(() => {
        showNotification('Lead information copied to clipboard!');
    }).catch(() => {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = leadInfo;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        showNotification('Lead information copied to clipboard!');
    });
}

// Export filtered leads to CSV
function exportToCSV() {
    if (filteredLeads.length === 0) {
        showNotification('No leads to export. Please adjust your filters.');
        return;
    }

    const headers = [
        'Score', 'Priority', 'Category', 'Providers', 'Phone', 
        'Address', 'ZIP', 'Population', 'Specialties'
    ];

    const csvContent = [
        headers.join(','),
        ...filteredLeads.map(lead => [
            lead.score,
            `"${lead.priority}"`,
            `"${lead.category}"`,
            lead.providers,
            `"${lead.phone || ''}"`,
            `"${lead.address || ''}"`,
            lead.zip,
            lead.population || '',
            `"${lead.specialties || ''}"`
        ].join(','))
    ].join('\n');

    downloadCSV(csvContent, 'rural_physician_leads.csv');
    showNotification(`Exported ${filteredLeads.length} leads to CSV`);
}

// Download CSV file
function downloadCSV(content, filename) {
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    
    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

// Download full dataset
function downloadFullDataset() {
    const link = document.createElement('a');
    link.href = '../rural_physician_leads_crm.xlsx';
    link.download = 'rural_physician_leads_complete.xlsx';
    link.click();
    showNotification('Downloading complete dataset...');
}

// Show loading overlay
function showLoadingOverlay() {
    document.getElementById('loading-overlay').classList.remove('hidden');
}

// Hide loading overlay
function hideLoadingOverlay() {
    document.getElementById('loading-overlay').classList.add('hidden');
}

// Show notification
function showNotification(message) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.innerHTML = `
        <i class="fas fa-check-circle"></i>
        <span>${message}</span>
    `;
    
    // Add to document
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 3000);
}

// Show error message
function showError(message) {
    const tbody = document.getElementById('leads-tbody');
    tbody.innerHTML = `
        <tr>
            <td colspan="10" class="error">
                <i class="fas fa-exclamation-triangle"></i>
                ${message}
            </td>
        </tr>
    `;
}

// Add notification styles
const notificationStyles = `
    .notification {
        position: fixed;
        top: 20px;
        right: 20px;
        background: #10b981;
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 1001;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        animation: slideIn 0.3s ease;
    }
    
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    .specialty-tag {
        display: inline-block;
        padding: 0.2rem 0.5rem;
        margin: 0.1rem;
        background: #f3f4f6;
        color: #374151;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 500;
    }
    
    .specialty-podiatrist {
        background: #dbeafe;
        color: #1e40af;
    }
    
    .specialty-wound-care {
        background: #fef3c7;
        color: #92400e;
    }
    
    .specialty-mohs {
        background: #f3e8ff;
        color: #7c3aed;
    }
    
    .error {
        color: #dc2626;
        text-align: center;
        font-style: italic;
    }
    
    .address-cell {
        max-width: 200px;
        word-wrap: break-word;
    }
    
    .specialties-cell {
        max-width: 250px;
    }
`;

// Add styles to document
const styleSheet = document.createElement('style');
styleSheet.textContent = notificationStyles;
document.head.appendChild(styleSheet); 