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
        populateFilterDropdowns();
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
    document.getElementById('a-plus-leads').textContent = summaryData.a_plus_leads?.toLocaleString() || '0';
    document.getElementById('podiatrist-groups').textContent = summaryData.podiatrist_groups?.toLocaleString() || '0';
    document.getElementById('wound-care-groups').textContent = summaryData.wound_care_groups?.toLocaleString() || '0';
}

// Populate filter dropdowns
function populateFilterDropdowns() {
    // Get unique states and cities
    const states = [...new Set(allLeads.map(lead => lead.state).filter(state => state && state !== 'N/A'))].sort();
    const cities = [...new Set(allLeads.map(lead => lead.city).filter(city => city && city !== 'N/A'))].sort();
    
    // Populate state filter
    const stateFilter = document.getElementById('state-filter');
    states.forEach(state => {
        const option = document.createElement('option');
        option.value = state;
        option.textContent = state;
        stateFilter.appendChild(option);
    });
    
    // Populate city filter
    const cityFilter = document.getElementById('city-filter');
    cities.forEach(city => {
        const option = document.createElement('option');
        option.value = city;
        option.textContent = city;
        cityFilter.appendChild(option);
    });
}

// Update last updated timestamp
function updateLastUpdated() {
    if (summaryData.last_updated) {
        const date = new Date(summaryData.last_updated);
        document.getElementById('last-updated').textContent = date.toLocaleString();
    }
}

// Setup event listeners
function setupEventListeners() {
    document.getElementById('priority-filter').addEventListener('change', applyFilters);
    document.getElementById('category-filter').addEventListener('change', applyFilters);
    document.getElementById('state-filter').addEventListener('change', applyFilters);
    document.getElementById('city-filter').addEventListener('change', applyFilters);
    document.getElementById('zip-filter').addEventListener('input', applyFilters);
    document.getElementById('search-filter').addEventListener('input', applyFilters);
}

// Apply filters to leads
function applyFilters() {
    const priorityFilter = document.getElementById('priority-filter').value;
    const categoryFilter = document.getElementById('category-filter').value;
    const stateFilter = document.getElementById('state-filter').value;
    const cityFilter = document.getElementById('city-filter').value;
    const zipFilter = document.getElementById('zip-filter').value.toLowerCase();
    const searchFilter = document.getElementById('search-filter').value.toLowerCase();

    filteredLeads = allLeads.filter(lead => {
        // Priority filter
        if (priorityFilter && lead.priority !== priorityFilter) {
            return false;
        }

        // Category filter
        if (categoryFilter && !lead.category.includes(categoryFilter)) {
            return false;
        }
        
        // State filter
        if (stateFilter && lead.state !== stateFilter) {
            return false;
        }
        
        // City filter
        if (cityFilter && lead.city !== cityFilter) {
            return false;
        }
        
        // ZIP filter
        if (zipFilter && !lead.zip.toLowerCase().includes(zipFilter)) {
            return false;
        }

        // Search filter (searches across multiple fields)
        if (searchFilter) {
            const searchFields = [
                lead.practice_name,
                lead.owner_name,
                lead.specialties,
                lead.category,
                lead.entity_type,
                lead.npi
            ].map(field => (field || '').toLowerCase());
            
            if (!searchFields.some(field => field.includes(searchFilter))) {
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
    document.getElementById('state-filter').value = '';
    document.getElementById('city-filter').value = '';
    document.getElementById('zip-filter').value = '';
    document.getElementById('search-filter').value = '';
    
    filteredLeads = [...allLeads];
    renderLeadsTable();
}

// Render the leads table
function renderLeadsTable() {
    const tbody = document.getElementById('leads-tbody');
    
    if (filteredLeads.length === 0) {
        tbody.innerHTML = '<tr><td colspan="13" class="loading">No leads match your filters.</td></tr>';
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
            <td>
                <div class="practice-name">
                    <strong>${lead.practice_name || 'N/A'}</strong>
                    ${lead.ein ? `<div class="ein-info">EIN: ${lead.ein}</div>` : ''}
                </div>
            </td>
            <td>
                <div class="owner-info">
                    ${lead.owner_name || 'N/A'}
                    ${lead.is_sole_proprietor === 'True' ? '<div class="sole-prop">Sole Proprietor</div>' : ''}
                </div>
            </td>
            <td>
                ${lead.practice_phone ? `<span class="phone-display">${lead.practice_phone}</span>` : '<span class="no-phone">N/A</span>'}
            </td>
            <td>
                ${lead.owner_phone ? `<span class="phone-display">${lead.owner_phone}</span>` : '<span class="no-phone">N/A</span>'}
            </td>
            <td>
                <span class="category-badge ${getCategoryClass(lead.category)}">
                    ${lead.category}
                </span>
            </td>
            <td>
                <strong>${lead.providers}</strong> provider${lead.providers > 1 ? 's' : ''}
            </td>
            <td>
                <div class="city-info">
                    ${lead.city || 'N/A'}
                </div>
            </td>
            <td>
                <div class="state-info">
                    ${lead.state || 'N/A'}
                </div>
            </td>
            <td><strong>${lead.zip}</strong></td>
            <td>
                <div class="entity-info">
                    ${lead.entity_type || 'N/A'}
                </div>
            </td>
            <td>
                <div class="action-buttons">
                    <button class="btn-copy" onclick="copyLeadInfo(${lead.id})" title="Copy Lead Info">
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
    if (score >= 70) return 'score-medium';
    return 'score-low';
}

// Get CSS class for priority badge
function getPriorityClass(priority) {
    if (priority === 'A+ Priority') return 'priority-a-plus';
    if (priority === 'A Priority') return 'priority-a';
    if (priority === 'B+ Priority') return 'priority-b-plus';
    return 'priority-b';
}

// Get CSS class for category badge
function getCategoryClass(category) {
    if (category.toLowerCase().includes('podiatrist')) return 'category-podiatrist';
    if (category.toLowerCase().includes('wound care')) return 'category-wound-care';
    if (category.toLowerCase().includes('mohs')) return 'category-mohs';
    return 'category-primary';
}

// Copy comprehensive lead information to clipboard
function copyLeadInfo(leadId) {
    const lead = allLeads.find(l => l.id === leadId);
    if (!lead) return;

    const leadInfo = `
COMPREHENSIVE LEAD INFORMATION
==============================
Practice Name: ${lead.practice_name || 'N/A'}
Owner/Contact: ${lead.owner_name || 'N/A'}
Entity Type: ${lead.entity_type || 'N/A'}
${lead.ein ? `EIN: ${lead.ein}` : ''}
NPI: ${lead.npi || 'N/A'}

CONTACT INFORMATION
===================
Practice Phone: ${lead.practice_phone || 'N/A'}
Owner Phone: ${lead.owner_phone || 'N/A'}
Address: ${lead.address || 'N/A'}
City: ${lead.city || 'N/A'}
State: ${lead.state || 'N/A'}
ZIP: ${lead.zip || 'N/A'}

BUSINESS DETAILS
================
Priority: ${lead.priority}
Category: ${lead.category}
Specialties: ${lead.specialties || 'N/A'}
Providers: ${lead.providers}
Score: ${lead.score}/100
${lead.is_sole_proprietor === 'True' ? 'Business Type: Sole Proprietor' : ''}
    `.trim();

    navigator.clipboard.writeText(leadInfo).then(() => {
        showNotification('Comprehensive lead information copied to clipboard!');
    }).catch(() => {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = leadInfo;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        showNotification('Comprehensive lead information copied to clipboard!');
    });
}

// Export filtered leads to CSV
function exportToCSV() {
    if (filteredLeads.length === 0) {
        showNotification('No leads to export. Please adjust your filters.');
        return;
    }

    const headers = [
        'Score', 'Priority', 'Practice Name', 'Owner/Contact', 'Practice Phone', 'Owner Phone',
        'Category', 'Providers', 'City', 'State', 'ZIP', 'Entity Type', 'NPI', 'EIN', 'Specialties',
        'Sole Proprietor'
    ];

    const csvContent = [
        headers.join(','),
        ...filteredLeads.map(lead => [
            lead.score,
            `"${lead.priority}"`,
            `"${lead.practice_name || ''}"`,
            `"${lead.owner_name || ''}"`,
            `"${lead.practice_phone || ''}"`,
            `"${lead.owner_phone || ''}"`,
            `"${lead.category}"`,
            lead.providers,
            `"${lead.city || ''}"`,
            `"${lead.state || ''}"`,
            lead.zip,
            `"${lead.entity_type || ''}"`,
            lead.npi || '',
            lead.ein || '',
            `"${lead.specialties || ''}"`,
            lead.is_sole_proprietor || ''
        ].join(','))
    ].join('\n');

    downloadCSV(csvContent, 'comprehensive_rural_physician_leads.csv');
    showNotification(`Exported ${filteredLeads.length} comprehensive leads to CSV`);
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
        URL.revokeObjectURL(url);
    }
}

// Show loading overlay
function showLoadingOverlay() {
    document.getElementById('loading-overlay').classList.add('visible');
}

// Hide loading overlay
function hideLoadingOverlay() {
    document.getElementById('loading-overlay').classList.remove('visible');
}

// Show notification
function showNotification(message) {
    // Create notification element if it doesn't exist
    let notification = document.querySelector('.notification');
    if (!notification) {
        notification = document.createElement('div');
        notification.className = 'notification';
        document.body.appendChild(notification);
    }
    
    notification.textContent = message;
    notification.classList.add('show');
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

// Show error message
function showError(message) {
    console.error(message);
    showNotification('Error: ' + message);
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