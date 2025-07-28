// Global variables
let allLeads = [];
let filteredLeads = [];
let summaryData = {};
let allCities = new Set();
let selectedCityFilter = '';
let currentCityIndex = -1;
let leadDataStorage = {}; // Store disposition and notes
let expandedLeads = new Set(); // Track which leads are expanded

// Authentication state
let authToken = null;
let currentUser = null;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    hideLoadingOverlay();
    initializeAuth();
    setupEventListeners();
});

        main
// Load data from backend API

// Authentication functions
function initializeAuth() {
    authToken = localStorage.getItem('auth_token');
    const userData = localStorage.getItem('user_data');
    
    if (authToken && userData) {
        try {
            currentUser = JSON.parse(userData);
            showDashboard();
            loadData();
        } catch (e) {
            console.error('Invalid user data:', e);
            showLogin();
        }
    } else {
        showLogin();
    }
}

function showLogin() {
    document.body.innerHTML = `
        <div class="login-container">
            <div class="login-card">
                <div class="login-header">
                    <h2><i class="fas fa-user-shield"></i> CRM Login</h2>
                    <p>Please enter your credentials</p>
                </div>
                <form id="loginForm">
                    <div class="form-group">
                        <label for="username">Username</label>
                        <input type="text" id="username" name="username" value="admin" required>
                    </div>
                    <div class="form-group">
                        <label for="password">Password</label>
                        <input type="password" id="password" name="password" value="admin123" required>
                    </div>
                    <button type="submit" class="login-btn">
                        <i class="fas fa-sign-in-alt"></i> Login
                    </button>
                    <div id="loginError" class="error-message" style="display: none;"></div>
                </form>
            </div>
        </div>
        <style>
            .login-container {
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            .login-card {
                background: white;
                padding: 2rem;
                border-radius: 12px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                width: 100%;
                max-width: 400px;
            }
            .login-header {
                text-align: center;
                margin-bottom: 2rem;
            }
            .login-header h2 {
                color: #333;
                margin: 0 0 0.5rem 0;
            }
            .login-header p {
                color: #666;
                margin: 0;
            }
            .form-group {
                margin-bottom: 1rem;
            }
            .form-group label {
                display: block;
                margin-bottom: 0.5rem;
                color: #333;
                font-weight: 500;
            }
            .form-group input {
                width: 100%;
                padding: 0.75rem;
                border: 2px solid #ddd;
                border-radius: 6px;
                font-size: 1rem;
                transition: border-color 0.3s;
            }
            .form-group input:focus {
                outline: none;
                border-color: #667eea;
            }
            .login-btn {
                width: 100%;
                padding: 0.75rem;
                background: #667eea;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 1rem;
                font-weight: 500;
                cursor: pointer;
                transition: background 0.3s;
            }
            .login-btn:hover {
                background: #5a67d8;
            }
            .error-message {
                color: #e53e3e;
                text-align: center;
                margin-top: 1rem;
                padding: 0.5rem;
                background: #fed7d7;
                border-radius: 4px;
            }
        </style>
    `;
    
    document.getElementById('loginForm').addEventListener('submit', handleLogin);
}

async function handleLogin(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorDiv = document.getElementById('loginError');
    
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}${CONFIG.ENDPOINTS.LOGIN}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });
        
        if (!response.ok) {
            throw new Error('Invalid credentials');
        }
        
        const data = await response.json();
        
        // Store authentication data
        authToken = data.access_token;
        currentUser = data.user;
        localStorage.setItem('auth_token', authToken);
        localStorage.setItem('user_data', JSON.stringify(currentUser));
        
        // Show dashboard
        showDashboard();
        loadData();
        
    } catch (error) {
        console.error('Login error:', error);
        errorDiv.textContent = 'Login failed. Please check your credentials.';
        errorDiv.style.display = 'block';
    }
}

function showDashboard() {
    // If we're already on the dashboard, just update the user info
    if (document.querySelector('.header')) {
        updateUserInfo();
        return;
    }
    // Otherwise reload to get the full dashboard
    window.location.reload();
}

function updateUserInfo() {
    if (currentUser) {
        const usernameDisplay = document.getElementById('username-display');
        if (usernameDisplay) {
            usernameDisplay.textContent = currentUser.username || 'User';
        }
    }
}

function logout() {
    authToken = null;
    currentUser = null;
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_data');
    showLogin();
}

// API helper function
async function apiCall(endpoint, options = {}) {
    const url = `${CONFIG.API_BASE_URL}${endpoint}`;
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };
    
    if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
    }
    
    try {
        const response = await fetch(url, {
            ...options,
            headers
        });
        
        if (response.status === 401) {
            logout();
            throw new Error('Authentication required');
        }
        
        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        throw error;
    }
}

// Load data from API instead of JSON files
async function loadData() {
    try {
        showLoadingOverlay();
        
        // Load all data from API endpoints
        const [leadsData, summaryData] = await Promise.all([
            apiCall(CONFIG.ENDPOINTS.LEADS),
            apiCall(CONFIG.ENDPOINTS.SUMMARY)
        ]);

        allLeads = leadsData.leads || [];
        summaryData = summaryData;
        
        // Initialize the UI
        updateUserInfo(); // Update user display
        updateDashboardStats();
        populateFilterDropdowns();
        filteredLeads = [...allLeads];
        renderLeadsTable();
        updateLastUpdated();
        loadLeadDataFromStorage(); // Load disposition and notes
        
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
    document.getElementById('goldmines').textContent = summaryData.goldmines?.toLocaleString() || '0';
    document.getElementById('high-value').textContent = summaryData.high_value?.toLocaleString() || '0';
    document.getElementById('perfect-scores').textContent = summaryData.perfect_scores?.toLocaleString() || '0';
}

// Populate filter dropdowns
function populateFilterDropdowns() {
    // Get unique states and cities
    const states = [...new Set(allLeads.map(lead => lead.state).filter(state => state && state !== 'N/A'))].sort();
    const cities = [...new Set(allLeads.map(lead => lead.city).filter(city => city && city !== 'N/A'))].sort();
    
    // Store cities for autocomplete
    allCities = new Set(cities);
    
    // Populate state filter
    const stateFilter = document.getElementById('state-filter');
    states.forEach(state => {
        const option = document.createElement('option');
        option.value = state;
        option.textContent = state;
        stateFilter.appendChild(option);
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
    document.getElementById('zip-filter').addEventListener('input', applyFilters);
    document.getElementById('search-filter').addEventListener('input', applyFilters);
    document.getElementById('disposition-filter').addEventListener('change', applyFilters);
    
    // City autocomplete functionality
    const cityInput = document.getElementById('city-filter');
    const citySuggestions = document.getElementById('city-suggestions');
    
    cityInput.addEventListener('input', function(e) {
        const value = e.target.value.toLowerCase().trim();
        
        if (value.length === 0) {
            citySuggestions.classList.remove('show');
            selectedCityFilter = '';
            applyFilters();
            return;
        }
        
        const matches = [...allCities].filter(city => 
            city.toLowerCase().includes(value)
        ).slice(0, 10).sort();
        
        if (matches.length > 0) {
            citySuggestions.innerHTML = matches.map(city => 
                `<div class="suggestion-item" data-city="${city}">${city}</div>`
            ).join('');
            citySuggestions.classList.add('show');
        } else {
            citySuggestions.innerHTML = '<div class="no-suggestions">No cities found</div>';
            citySuggestions.classList.add('show');
        }
        
        currentCityIndex = -1;
    });
    
    // Handle city selection
    citySuggestions.addEventListener('click', function(e) {
        if (e.target.classList.contains('suggestion-item')) {
            const city = e.target.dataset.city;
            cityInput.value = city;
            selectedCityFilter = city;
            citySuggestions.classList.remove('show');
            applyFilters();
        }
    });
    
    // Handle keyboard navigation
    cityInput.addEventListener('keydown', function(e) {
        const suggestions = citySuggestions.querySelectorAll('.suggestion-item');
        
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            currentCityIndex = Math.min(currentCityIndex + 1, suggestions.length - 1);
            updateHighlight(suggestions);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            currentCityIndex = Math.max(currentCityIndex - 1, -1);
            updateHighlight(suggestions);
        } else if (e.key === 'Enter') {
            e.preventDefault();
            if (currentCityIndex >= 0 && suggestions[currentCityIndex]) {
                const city = suggestions[currentCityIndex].dataset.city;
                cityInput.value = city;
                selectedCityFilter = city;
                citySuggestions.classList.remove('show');
                applyFilters();
            }
        } else if (e.key === 'Escape') {
            citySuggestions.classList.remove('show');
        }
    });
    
    // Hide suggestions when clicking outside
    document.addEventListener('click', function(e) {
        if (!cityInput.contains(e.target) && !citySuggestions.contains(e.target)) {
            citySuggestions.classList.remove('show');
        }
    });
}

// Update highlight for keyboard navigation
function updateHighlight(suggestions) {
    suggestions.forEach((item, index) => {
        if (index === currentCityIndex) {
            item.classList.add('highlighted');
        } else {
            item.classList.remove('highlighted');
        }
    });
}

// Apply filters to leads
function applyFilters() {
    const priorityFilter = document.getElementById('priority-filter').value;
    const categoryFilter = document.getElementById('category-filter').value;
    const stateFilter = document.getElementById('state-filter').value;
    const zipFilter = document.getElementById('zip-filter').value.toLowerCase();
    const searchFilter = document.getElementById('search-filter').value.toLowerCase();
    const dispositionFilter = document.getElementById('disposition-filter').value;

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
        
        // City filter (now uses autocomplete)
        if (selectedCityFilter && lead.city !== selectedCityFilter) {
            return false;
        }
        
        // ZIP filter
        if (zipFilter && !lead.zip.toLowerCase().includes(zipFilter)) {
            return false;
        }

        // Disposition filter
        if (dispositionFilter) {
            const leadData = getLeadData(lead.id);
            if (dispositionFilter === 'no-disposition') {
                if (leadData.disposition) {
                    return false;
                }
            } else if (leadData.disposition !== dispositionFilter) {
                return false;
            }
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
    document.getElementById('disposition-filter').value = '';
    
    // Reset city autocomplete
    selectedCityFilter = '';
    document.getElementById('city-suggestions').classList.remove('show');
    
    filteredLeads = [...allLeads];
    renderLeadsTable();
}

// Collapse all expanded leads
function collapseAllLeads() {
    expandedLeads.clear();
    renderLeadsTable();
    showNotification('All leads collapsed');
}

// Render the leads table
function renderLeadsTable() {
    const tbody = document.getElementById('leads-tbody');
    
    if (filteredLeads.length === 0) {
        tbody.innerHTML = '<tr><td colspan="15" class="loading">No leads match your filters.</td></tr>';
        return;
    }

    tbody.innerHTML = filteredLeads.map(lead => {
        const leadData = getLeadData(lead.id);
        const isExpanded = expandedLeads.has(lead.id);
        
        return `
        <tr class="lead-row ${isExpanded ? 'expanded' : ''}" data-lead-id="${lead.id}">
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
                <div class="practice-name clickable" data-lead-id="${lead.id}" data-action="toggle-expand">
                    <strong>${lead.practice_name || 'N/A'}</strong>
                    <i class="fas fa-chevron-${isExpanded ? 'up' : 'down'} expand-icon"></i>
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
                <select class="disposition-select" data-value="${leadData.disposition || ''}" data-lead-id="${lead.id}" data-action="update-disposition">
                    <option value="">Select...</option>
                    <option value="appointment-made" ${leadData.disposition === 'appointment-made' ? 'selected' : ''}>Appointment Made</option>
                    <option value="onboarded" ${leadData.disposition === 'onboarded' ? 'selected' : ''}>Onboarded</option>
                    <option value="do-not-call" ${leadData.disposition === 'do-not-call' ? 'selected' : ''}>Do Not Call</option>
                    <option value="bad-phone" ${leadData.disposition === 'bad-phone' ? 'selected' : ''}>Bad Phone Number</option>
                    <option value="no-answer" ${leadData.disposition === 'no-answer' ? 'selected' : ''}>No Answer</option>
                    <option value="callback" ${leadData.disposition === 'callback' ? 'selected' : ''}>Callback Requested</option>
                    <option value="not-interested" ${leadData.disposition === 'not-interested' ? 'selected' : ''}>Not Interested</option>
                </select>
            </td>
            <td>
                <textarea class="notes-input" placeholder="Add notes..." 
                    data-lead-id="${lead.id}" data-action="update-notes"
                    oninput="autoResize(this)">${leadData.notes || ''}</textarea>
            </td>
            <td>
                <div class="action-buttons">
                    <button class="btn-edit" data-lead-id="${lead.id}" data-action="edit-lead" title="Edit Lead">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn-copy" data-lead-id="${lead.id}" data-action="copy-lead" title="Copy Lead Info">
                        <i class="fas fa-copy"></i>
                    </button>
                    <button class="btn-expand" data-lead-id="${lead.id}" data-action="toggle-expand" title="View Details">
                        <i class="fas fa-${isExpanded ? 'compress' : 'expand'}"></i>
                    </button>
                </div>
            </td>
        </tr>
        ${isExpanded ? renderLeadDetailRow(lead) : ''}
    `;}).join('');
    
    // Add event delegation for all buttons and interactions
    setupTableEventListeners();
}

// Setup table event listeners with delegation
function setupTableEventListeners() {
    const tbody = document.getElementById('leads-tbody');
    
    // Remove existing listeners to prevent duplicates
    tbody.removeEventListener('click', handleTableClick);
    tbody.removeEventListener('change', handleTableChange);
    tbody.removeEventListener('blur', handleTableBlur, true);
    
    // Add event listeners
    tbody.addEventListener('click', handleTableClick);
    tbody.addEventListener('change', handleTableChange);
    tbody.addEventListener('blur', handleTableBlur, true);
}

// Handle all table clicks
function handleTableClick(event) {
    const target = event.target.closest('[data-action]');
    if (!target) return;
    
    const action = target.dataset.action;
    const leadId = target.dataset.leadId;
    
    switch (action) {
        case 'toggle-expand':
            toggleLeadExpansion(parseInt(leadId));
            break;
        case 'edit-lead':
            openLeadEditModal(parseInt(leadId));
            break;
        case 'copy-lead':
            copyLeadInfo(parseInt(leadId));
            break;
        case 'export-lead':
            exportSingleLead(parseInt(leadId));
            break;
        case 'open-maps':
            const address = decodeURIComponent(target.dataset.address);
            openGoogleMaps(address);
            break;
        case 'search-online':
            const practice = decodeURIComponent(target.dataset.practice);
            const city = decodeURIComponent(target.dataset.city);
            const state = decodeURIComponent(target.dataset.state);
            searchPracticeOnline(practice, city, state);
            break;
    }
    
    // Handle copy field buttons
    if (target.classList.contains('btn-copy-field')) {
        const text = decodeURIComponent(target.dataset.copyText);
        const fieldName = target.dataset.fieldName;
        copyToClipboard(text, fieldName);
    }
}

// Handle form changes
function handleTableChange(event) {
    const target = event.target;
    if (target.dataset.action === 'update-disposition') {
        const leadId = parseInt(target.dataset.leadId);
        updateDisposition(leadId, target.value);
    }
}

// Handle blur events (for notes)
function handleTableBlur(event) {
    const target = event.target;
    if (target.dataset.action === 'update-notes') {
        const leadId = parseInt(target.dataset.leadId);
        updateNotes(leadId, target.value);
    }
}

// Toggle lead expansion
function toggleLeadExpansion(leadId) {
    if (expandedLeads.has(leadId)) {
        expandedLeads.delete(leadId);
    } else {
        expandedLeads.add(leadId);
    }
    renderLeadsTable(); // Re-render to show/hide details
}

// Render detailed lead information row
function renderLeadDetailRow(lead) {
    return `
        <tr class="lead-detail-row" data-lead-id="${lead.id}">
            <td colspan="15">
                <div class="lead-detail-content">
                    <div class="detail-sections">
                        <!-- Provider Identity Section -->
                        <div class="detail-section">
                            <h4><i class="fas fa-id-card"></i> Provider Identity</h4>
                            <div class="detail-grid">
                                <div class="detail-item">
                                    <label>NPI:</label>
                                    <span class="detail-value npi-value">${lead.npi || 'N/A'}</span>
                                    ${lead.npi ? `<button class="btn-copy-field" data-copy-text="${lead.npi}" data-field-name="NPI" title="Copy NPI"><i class="fas fa-copy"></i></button>` : ''}
                                </div>
                                <div class="detail-item">
                                    <label>EIN:</label>
                                    <span class="detail-value">${lead.ein || 'N/A'}</span>
                                    ${lead.ein ? `<button class="btn-copy-field" data-copy-text="${lead.ein}" data-field-name="EIN" title="Copy EIN"><i class="fas fa-copy"></i></button>` : ''}
                                </div>
                                <div class="detail-item">
                                    <label>Entity Type:</label>
                                    <span class="detail-value">${lead.entity_type || 'N/A'}</span>
                                </div>
                                <div class="detail-item">
                                    <label>Sole Proprietor:</label>
                                    <span class="detail-value">${lead.is_sole_proprietor === 'True' ? 'Yes' : 'No'}</span>
                                </div>
                            </div>
                        </div>

                        <!-- Contact Information Section -->
                        <div class="detail-section">
                            <h4><i class="fas fa-phone"></i> Contact Information</h4>
                            <div class="detail-grid">
                                <div class="detail-item">
                                    <label>Practice Phone:</label>
                                    <span class="detail-value phone-value">${lead.practice_phone || 'N/A'}</span>
                                    ${lead.practice_phone ? `<button class="btn-copy-field" data-copy-text="${lead.practice_phone}" data-field-name="Practice Phone" title="Copy Phone"><i class="fas fa-copy"></i></button>` : ''}
                                </div>
                                <div class="detail-item">
                                    <label>Owner Phone:</label>
                                    <span class="detail-value phone-value">${lead.owner_phone || 'N/A'}</span>
                                    ${lead.owner_phone ? `<button class="btn-copy-field" data-copy-text="${lead.owner_phone}" data-field-name="Owner Phone" title="Copy Phone"><i class="fas fa-copy"></i></button>` : ''}
                                </div>
                                <div class="detail-item full-width">
                                    <label>Full Address:</label>
                                    <span class="detail-value address-value">${lead.address || 'N/A'}</span>
                                    ${lead.address ? `<button class="btn-copy-field" data-copy-text="${encodeURIComponent(lead.address)}" data-field-name="Address" title="Copy Address"><i class="fas fa-copy"></i></button>` : ''}
                                </div>
                            </div>
                        </div>

                        <!-- Business Details Section -->
                        <div class="detail-section">
                            <h4><i class="fas fa-building"></i> Business Details</h4>
                            <div class="detail-grid">
                                <div class="detail-item">
                                    <label>Practice Name:</label>
                                    <span class="detail-value">${lead.practice_name || 'N/A'}</span>
                                </div>
                                <div class="detail-item">
                                    <label>Owner/Contact:</label>
                                    <span class="detail-value">${lead.owner_name || 'N/A'}</span>
                                </div>
                                <div class="detail-item">
                                    <label>Provider Count:</label>
                                    <span class="detail-value">${lead.providers} provider${lead.providers > 1 ? 's' : ''}</span>
                                </div>
                                <div class="detail-item">
                                    <label>Primary Category:</label>
                                    <span class="detail-value">${lead.category}</span>
                                </div>
                                <div class="detail-item full-width">
                                    <label>All Specialties:</label>
                                    <span class="detail-value specialties-value">${lead.specialties || 'N/A'}</span>
                                </div>
                            </div>
                        </div>

                        <!-- Scoring & Priority Section -->
                        <div class="detail-section">
                            <h4><i class="fas fa-star"></i> Scoring & Priority</h4>
                            <div class="detail-grid">
                                <div class="detail-item">
                                    <label>Lead Score:</label>
                                    <span class="detail-value score-large ${getScoreClass(lead.score)}">${lead.score}/100</span>
                                </div>
                                <div class="detail-item">
                                    <label>Priority Level:</label>
                                    <span class="detail-value priority-large ${getPriorityClass(lead.priority)}">${lead.priority}</span>
                                </div>
                                <div class="detail-item">
                                    <label>Geographic Region:</label>
                                    <span class="detail-value">${lead.city}, ${lead.state} ${lead.zip}</span>
                                </div>
                                <div class="detail-item">
                                    <label>Lead ID:</label>
                                    <span class="detail-value">#${lead.id}</span>
                                </div>
                            </div>
                        </div>

                        <!-- Quick Actions Section -->
                        <div class="detail-section">
                            <h4><i class="fas fa-bolt"></i> Quick Actions</h4>
                            <div class="quick-actions">
                                <button class="btn-action" data-action="open-maps" data-address="${encodeURIComponent(lead.address || '')}" title="View on Google Maps">
                                    <i class="fas fa-map-marker-alt"></i> View Location
                                </button>
                                <button class="btn-action" data-action="search-online" data-practice="${encodeURIComponent(lead.practice_name || '')}" data-city="${encodeURIComponent(lead.city || '')}" data-state="${encodeURIComponent(lead.state || '')}" title="Search Practice Online">
                                    <i class="fas fa-search"></i> Search Online
                                </button>
                                <button class="btn-action" data-action="copy-lead" data-lead-id="${lead.id}" title="Copy All Lead Info">
                                    <i class="fas fa-copy"></i> Copy All Info
                                </button>
                                <button class="btn-action" data-action="export-lead" data-lead-id="${lead.id}" title="Export Lead">
                                    <i class="fas fa-download"></i> Export Lead
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </td>
        </tr>
    `;
}

// Copy individual field to clipboard
function copyToClipboard(text, fieldName) {
    if (!text || text === 'N/A') {
        showNotification(`No ${fieldName} to copy`);
        return;
    }
    
    navigator.clipboard.writeText(text).then(() => {
        showNotification(`${fieldName} copied: ${text}`);
    }).catch(() => {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        showNotification(`${fieldName} copied: ${text}`);
    });
}

// Open Google Maps for address
function openGoogleMaps(address) {
    if (!address || address === 'N/A') {
        showNotification('No address available');
        return;
    }
    const encodedAddress = encodeURIComponent(address);
    window.open(`https://maps.google.com/?q=${encodedAddress}`, '_blank');
}

// Search practice online
function searchPracticeOnline(practiceName, city, state) {
    if (!practiceName || practiceName === 'N/A') {
        showNotification('No practice name available');
        return;
    }
    const searchQuery = `"${practiceName}" ${city} ${state}`;
    const encodedQuery = encodeURIComponent(searchQuery);
    window.open(`https://www.google.com/search?q=${encodedQuery}`, '_blank');
}

// Export single lead
function exportSingleLead(leadId) {
    const lead = allLeads.find(l => l.id === leadId);
    if (!lead) return;

    const leadData = getLeadData(leadId);
    
    const csvContent = [
        ['Field', 'Value'],
        ['Lead ID', lead.id],
        ['Score', lead.score],
        ['Priority', lead.priority],
        ['Practice Name', lead.practice_name || ''],
        ['Owner/Contact', lead.owner_name || ''],
        ['NPI', lead.npi || ''],
        ['EIN', lead.ein || ''],
        ['Entity Type', lead.entity_type || ''],
        ['Practice Phone', lead.practice_phone || ''],
        ['Owner Phone', lead.owner_phone || ''],
        ['Category', lead.category],
        ['Specialties', lead.specialties || ''],
        ['Providers', lead.providers],
        ['Address', lead.address || ''],
        ['City', lead.city || ''],
        ['State', lead.state || ''],
        ['ZIP', lead.zip],
        ['Sole Proprietor', lead.is_sole_proprietor || ''],
        ['Disposition', leadData.disposition || ''],
        ['Notes', leadData.notes || '']
    ].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');

    downloadCSV(csvContent, `lead_${leadId}_${lead.practice_name || 'unknown'}.csv`);
    showNotification(`Lead #${leadId} exported successfully`);
}

// Get lead data from storage
function getLeadData(leadId) {
    return leadDataStorage[leadId] || { disposition: '', notes: '' };
}

// Update disposition for a lead
function updateDisposition(leadId, disposition) {
    if (!leadDataStorage[leadId]) {
        leadDataStorage[leadId] = { disposition: '', notes: '' };
    }
    leadDataStorage[leadId].disposition = disposition;
    saveLeadDataToStorage();
    
    // Update visual styling of the dropdown
    const selectElement = event.target;
    selectElement.setAttribute('data-value', disposition);
    
    showNotification(`Disposition updated: ${getDispositionLabel(disposition)}`);
}

// Update notes for a lead
function updateNotes(leadId, notes) {
    if (!leadDataStorage[leadId]) {
        leadDataStorage[leadId] = { disposition: '', notes: '' };
    }
    leadDataStorage[leadId].notes = notes;
    saveLeadDataToStorage();
}

// Get human-readable disposition label
function getDispositionLabel(disposition) {
    const labels = {
        'appointment-made': 'Appointment Made',
        'onboarded': 'Onboarded',
        'do-not-call': 'Do Not Call',
        'bad-phone': 'Bad Phone Number',
        'no-answer': 'No Answer',
        'callback': 'Callback Requested',
        'not-interested': 'Not Interested'
    };
    return labels[disposition] || disposition;
}

// Auto-resize textarea
function autoResize(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
}

// Save lead data to localStorage
function saveLeadDataToStorage() {
    localStorage.setItem('leadDataStorage', JSON.stringify(leadDataStorage));
}

// Load lead data from localStorage
function loadLeadDataFromStorage() {
    const stored = localStorage.getItem('leadDataStorage');
    if (stored) {
        leadDataStorage = JSON.parse(stored);
    }
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

    const leadData = getLeadData(leadId);

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
Disposition: ${leadData.disposition ? getDispositionLabel(leadData.disposition) : 'N/A'}
Notes: ${leadData.notes || 'N/A'}
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
        'Sole Proprietor', 'Disposition', 'Notes'
    ];

    const csvContent = [
        headers.join(','),
        ...filteredLeads.map(lead => {
            const leadData = getLeadData(lead.id);
            return [
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
                lead.is_sole_proprietor || '',
                `"${leadData.disposition || ''}"`,
                `"${leadData.notes || ''}"`
            ].join(',');
        })
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