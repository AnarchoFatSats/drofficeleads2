/*!
 * Enhanced CRM Components - Performance & User Experience
 * Advanced UI components for VantagePoint
 */

// ====================================
// 1. LOADING STATES & SKELETON SCREENS
// ====================================

class LoadingStates {
    static createSkeleton(type = 'default') {
        const skeletons = {
            default: `
                <div class="skeleton-container">
                    <div class="skeleton-line skeleton-line-long"></div>
                    <div class="skeleton-line skeleton-line-medium"></div>
                    <div class="skeleton-line skeleton-line-short"></div>
                </div>`,
            card: `
                <div class="skeleton-card">
                    <div class="skeleton-header"></div>
                    <div class="skeleton-content">
                        <div class="skeleton-line skeleton-line-long"></div>
                        <div class="skeleton-line skeleton-line-medium"></div>
                        <div class="skeleton-line skeleton-line-short"></div>
                    </div>
                </div>`,
            table: `
                <div class="skeleton-table">
                    <div class="skeleton-table-header">
                        <div class="skeleton-cell"></div>
                        <div class="skeleton-cell"></div>
                        <div class="skeleton-cell"></div>
                        <div class="skeleton-cell"></div>
                    </div>
                    <div class="skeleton-table-row">
                        <div class="skeleton-cell"></div>
                        <div class="skeleton-cell"></div>
                        <div class="skeleton-cell"></div>
                        <div class="skeleton-cell"></div>
                    </div>
                    <div class="skeleton-table-row">
                        <div class="skeleton-cell"></div>
                        <div class="skeleton-cell"></div>
                        <div class="skeleton-cell"></div>
                        <div class="skeleton-cell"></div>
                    </div>
                </div>`,
            chart: `
                <div class="skeleton-chart">
                    <div class="skeleton-chart-bars">
                        <div class="skeleton-bar" style="height: 60%"></div>
                        <div class="skeleton-bar" style="height: 80%"></div>
                        <div class="skeleton-bar" style="height: 40%"></div>
                        <div class="skeleton-bar" style="height: 90%"></div>
                        <div class="skeleton-bar" style="height: 70%"></div>
                    </div>
                </div>`
        };
        return skeletons[type] || skeletons.default;
    }

    static showLoading(containerId, type = 'default') {
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = this.createSkeleton(type);
            container.classList.add('loading-state');
        }
    }

    static hideLoading(containerId) {
        const container = document.getElementById(containerId);
        if (container) {
            container.classList.remove('loading-state');
        }
    }

    static createProgressIndicator(progress = 0) {
        return `
            <div class="progress-indicator">
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${progress}%"></div>
                </div>
                <div class="progress-text">${progress}%</div>
            </div>`;
    }
}

// ====================================
// 2. ERROR BOUNDARIES & ERROR HANDLING
// ====================================

class ErrorHandler {
    static showError(message, type = 'error', duration = 5000) {
        const errorContainer = document.getElementById('error-container') || this.createErrorContainer();
        
        const errorElement = document.createElement('div');
        errorElement.className = `alert alert-${type} alert-dismissible fade show`;
        errorElement.innerHTML = `
            <div class="alert-icon">
                <i class="fas fa-${this.getIcon(type)}"></i>
            </div>
            <div class="alert-content">
                <strong>${this.getTitle(type)}</strong>
                <p>${message}</p>
            </div>
            <button type="button" class="btn-close" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;

        errorContainer.appendChild(errorElement);

        if (duration > 0) {
            setTimeout(() => {
                if (errorElement.parentNode) {
                    errorElement.remove();
                }
            }, duration);
        }
    }

    static createErrorContainer() {
        const container = document.createElement('div');
        container.id = 'error-container';
        container.className = 'error-container';
        document.body.appendChild(container);
        return container;
    }

    static getIcon(type) {
        const icons = {
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            success: 'check-circle',
            info: 'info-circle'
        };
        return icons[type] || 'exclamation-circle';
    }

    static getTitle(type) {
        const titles = {
            error: 'Error',
            warning: 'Warning',
            success: 'Success',
            info: 'Information'
        };
        return titles[type] || 'Error';
    }

    static handleAPIError(error, context = '') {
        console.error(`API Error ${context}:`, error);
        
        let message = 'An unexpected error occurred. Please try again.';
        
        if (error.response) {
            // Server responded with error status
            const status = error.response.status;
            const data = error.response.data;
            
            if (status === 401) {
                message = 'Session expired. Please log in again.';
                setTimeout(() => window.location.href = '/login', 2000);
            } else if (status === 403) {
                message = 'You do not have permission to perform this action.';
            } else if (status === 404) {
                message = 'The requested resource was not found.';
            } else if (status === 500) {
                message = 'Server error. Please try again later.';
            } else if (data && data.detail) {
                message = data.detail;
            }
        } else if (error.request) {
            // Request made but no response
            message = 'Network error. Please check your connection.';
        }

        this.showError(message, 'error');
    }
}

// ====================================
// 3. ADVANCED SEARCH & FILTERING
// ====================================

class AdvancedSearch {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            placeholder: 'Search leads...',
            fields: ['practice_name', 'owner_name', 'city', 'state', 'specialties'],
            filters: [],
            realTime: true,
            debounceDelay: 300,
            ...options
        };
        this.searchTimeout = null;
        this.filters = {};
        this.init();
    }

    init() {
        this.render();
        this.attachEvents();
    }

    render() {
        this.container.innerHTML = `
            <div class="advanced-search">
                <div class="search-input-container">
                    <div class="search-input-wrapper">
                        <i class="fas fa-search search-icon"></i>
                        <input type="text" 
                               id="search-input" 
                               class="search-input" 
                               placeholder="${this.options.placeholder}">
                        <button class="search-clear" id="search-clear" style="display: none;">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <button class="filter-toggle" id="filter-toggle">
                        <i class="fas fa-filter"></i>
                        Filters
                        <span class="filter-count" id="filter-count" style="display: none;">0</span>
                    </button>
                </div>
                
                <div class="search-filters" id="search-filters" style="display: none;">
                    <div class="filter-grid">
                        ${this.renderFilters()}
                    </div>
                    <div class="filter-actions">
                        <button class="btn btn-secondary" id="clear-filters">Clear All</button>
                        <button class="btn btn-primary" id="apply-filters">Apply Filters</button>
                    </div>
                </div>

                <div class="search-suggestions" id="search-suggestions" style="display: none;">
                    <!-- Dynamic suggestions will be populated here -->
                </div>
            </div>
        `;
    }

    renderFilters() {
        return this.options.filters.map(filter => {
            switch (filter.type) {
                case 'select':
                    return this.renderSelectFilter(filter);
                case 'range':
                    return this.renderRangeFilter(filter);
                case 'date':
                    return this.renderDateFilter(filter);
                case 'checkbox':
                    return this.renderCheckboxFilter(filter);
                default:
                    return this.renderTextFilter(filter);
            }
        }).join('');
    }

    renderSelectFilter(filter) {
        return `
            <div class="filter-group">
                <label class="filter-label">${filter.label}</label>
                <select class="filter-select" data-filter="${filter.field}">
                    <option value="">All ${filter.label}</option>
                    ${filter.options.map(option => 
                        `<option value="${option.value}">${option.label}</option>`
                    ).join('')}
                </select>
            </div>
        `;
    }

    renderRangeFilter(filter) {
        return `
            <div class="filter-group">
                <label class="filter-label">${filter.label}</label>
                <div class="range-inputs">
                    <input type="number" class="filter-input" 
                           placeholder="Min" data-filter="${filter.field}_min">
                    <span class="range-separator">to</span>
                    <input type="number" class="filter-input" 
                           placeholder="Max" data-filter="${filter.field}_max">
                </div>
            </div>
        `;
    }

    renderDateFilter(filter) {
        return `
            <div class="filter-group">
                <label class="filter-label">${filter.label}</label>
                <div class="date-inputs">
                    <input type="date" class="filter-input" data-filter="${filter.field}_start">
                    <span class="date-separator">to</span>
                    <input type="date" class="filter-input" data-filter="${filter.field}_end">
                </div>
            </div>
        `;
    }

    renderCheckboxFilter(filter) {
        return `
            <div class="filter-group">
                <label class="filter-label">${filter.label}</label>
                <div class="checkbox-group">
                    ${filter.options.map(option => `
                        <label class="checkbox-label">
                            <input type="checkbox" class="filter-checkbox" 
                                   value="${option.value}" data-filter="${filter.field}">
                            <span class="checkbox-text">${option.label}</span>
                        </label>
                    `).join('')}
                </div>
            </div>
        `;
    }

    renderTextFilter(filter) {
        return `
            <div class="filter-group">
                <label class="filter-label">${filter.label}</label>
                <input type="text" class="filter-input" 
                       placeholder="Enter ${filter.label.toLowerCase()}" 
                       data-filter="${filter.field}">
            </div>
        `;
    }

    attachEvents() {
        const searchInput = document.getElementById('search-input');
        const filterToggle = document.getElementById('filter-toggle');
        const searchFilters = document.getElementById('search-filters');
        const clearFilters = document.getElementById('clear-filters');
        const applyFilters = document.getElementById('apply-filters');
        const searchClear = document.getElementById('search-clear');

        // Real-time search
        searchInput.addEventListener('input', (e) => {
            const value = e.target.value;
            searchClear.style.display = value ? 'block' : 'none';
            
            if (this.options.realTime) {
                clearTimeout(this.searchTimeout);
                this.searchTimeout = setTimeout(() => {
                    this.performSearch(value);
                }, this.options.debounceDelay);
            }
        });

        // Clear search
        searchClear.addEventListener('click', () => {
            searchInput.value = '';
            searchClear.style.display = 'none';
            this.performSearch('');
        });

        // Toggle filters
        filterToggle.addEventListener('click', () => {
            const isVisible = searchFilters.style.display !== 'none';
            searchFilters.style.display = isVisible ? 'none' : 'block';
        });

        // Clear all filters
        clearFilters.addEventListener('click', () => {
            this.clearAllFilters();
        });

        // Apply filters
        applyFilters.addEventListener('click', () => {
            this.applyFilters();
        });

        // Filter inputs
        this.container.addEventListener('change', (e) => {
            if (e.target.matches('.filter-select, .filter-input, .filter-checkbox')) {
                this.updateFilterCount();
            }
        });
    }

    performSearch(query) {
        const filters = this.getActiveFilters();
        
        // Trigger search event
        const searchEvent = new CustomEvent('search', {
            detail: { query, filters }
        });
        this.container.dispatchEvent(searchEvent);
    }

    getActiveFilters() {
        const filters = {};
        
        // Text filters
        this.container.querySelectorAll('.filter-input').forEach(input => {
            if (input.value.trim()) {
                filters[input.dataset.filter] = input.value.trim();
            }
        });

        // Select filters
        this.container.querySelectorAll('.filter-select').forEach(select => {
            if (select.value) {
                filters[select.dataset.filter] = select.value;
            }
        });

        // Checkbox filters
        const checkboxGroups = {};
        this.container.querySelectorAll('.filter-checkbox:checked').forEach(checkbox => {
            const field = checkbox.dataset.filter;
            if (!checkboxGroups[field]) {
                checkboxGroups[field] = [];
            }
            checkboxGroups[field].push(checkbox.value);
        });

        Object.assign(filters, checkboxGroups);
        return filters;
    }

    clearAllFilters() {
        this.container.querySelectorAll('.filter-input').forEach(input => input.value = '');
        this.container.querySelectorAll('.filter-select').forEach(select => select.selectedIndex = 0);
        this.container.querySelectorAll('.filter-checkbox').forEach(checkbox => checkbox.checked = false);
        this.updateFilterCount();
        this.performSearch(document.getElementById('search-input').value);
    }

    applyFilters() {
        this.performSearch(document.getElementById('search-input').value);
        document.getElementById('search-filters').style.display = 'none';
    }

    updateFilterCount() {
        const activeFilters = Object.keys(this.getActiveFilters()).length;
        const filterCount = document.getElementById('filter-count');
        
        if (activeFilters > 0) {
            filterCount.textContent = activeFilters;
            filterCount.style.display = 'inline';
        } else {
            filterCount.style.display = 'none';
        }
    }
}

// ====================================
// 4. INTERACTIVE CHARTS WITH DRILL-DOWN
// ====================================

class InteractiveCharts {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            type: 'bar',
            drillDown: true,
            animations: true,
            ...options
        };
        this.currentLevel = 0;
        this.drillStack = [];
        this.init();
    }

    init() {
        this.render();
        this.attachEvents();
    }

    render() {
        this.container.innerHTML = `
            <div class="interactive-chart">
                <div class="chart-header">
                    <div class="chart-title-section">
                        <h3 class="chart-title">${this.options.title || 'Chart'}</h3>
                        <div class="chart-breadcrumb" id="chart-breadcrumb">
                            <span class="breadcrumb-item active">Overview</span>
                        </div>
                    </div>
                    <div class="chart-controls">
                        <button class="btn btn-sm btn-outline-secondary" id="chart-back" style="display: none;">
                            <i class="fas fa-arrow-left"></i> Back
                        </button>
                        <div class="chart-type-selector">
                            <button class="chart-type-btn ${this.options.type === 'bar' ? 'active' : ''}" data-type="bar">
                                <i class="fas fa-chart-bar"></i>
                            </button>
                            <button class="chart-type-btn ${this.options.type === 'line' ? 'active' : ''}" data-type="line">
                                <i class="fas fa-chart-line"></i>
                            </button>
                            <button class="chart-type-btn ${this.options.type === 'pie' ? 'active' : ''}" data-type="pie">
                                <i class="fas fa-chart-pie"></i>
                            </button>
                        </div>
                        <button class="btn btn-sm btn-outline-primary" id="chart-export">
                            <i class="fas fa-download"></i> Export
                        </button>
                    </div>
                </div>
                <div class="chart-container" id="chart-canvas">
                    <!-- Chart will be rendered here -->
                </div>
                <div class="chart-legend" id="chart-legend">
                    <!-- Legend will be populated dynamically -->
                </div>
            </div>
        `;
    }

    attachEvents() {
        // Chart type switching
        this.container.addEventListener('click', (e) => {
            if (e.target.matches('.chart-type-btn')) {
                this.switchChartType(e.target.dataset.type);
            }
        });

        // Back navigation
        document.getElementById('chart-back').addEventListener('click', () => {
            this.navigateBack();
        });

        // Export
        document.getElementById('chart-export').addEventListener('click', () => {
            this.exportChart();
        });
    }

    switchChartType(type) {
        this.options.type = type;
        
        // Update active button
        this.container.querySelectorAll('.chart-type-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.type === type);
        });

        // Re-render chart
        this.renderChart(this.currentData);
    }

    renderChart(data) {
        this.currentData = data;
        const canvas = document.getElementById('chart-canvas');
        
        // Show loading
        LoadingStates.showLoading('chart-canvas', 'chart');

        // Simulate chart rendering (replace with actual chart library)
        setTimeout(() => {
            canvas.innerHTML = this.generateChartHTML(data);
            LoadingStates.hideLoading('chart-canvas');
            this.attachChartEvents();
        }, 500);
    }

    generateChartHTML(data) {
        switch (this.options.type) {
            case 'bar':
                return this.generateBarChart(data);
            case 'line':
                return this.generateLineChart(data);
            case 'pie':
                return this.generatePieChart(data);
            default:
                return this.generateBarChart(data);
        }
    }

    generateBarChart(data) {
        const maxValue = Math.max(...data.map(item => item.value));
        
        return `
            <div class="bar-chart">
                ${data.map((item, index) => `
                    <div class="bar-group" data-drill="${item.drillData ? 'true' : 'false'}" data-index="${index}">
                        <div class="bar-container">
                            <div class="bar" style="height: ${(item.value / maxValue) * 100}%">
                                <div class="bar-value">${item.value}</div>
                            </div>
                        </div>
                        <div class="bar-label">${item.label}</div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    generateLineChart(data) {
        return `
            <div class="line-chart">
                <svg viewBox="0 0 400 200" class="line-chart-svg">
                    <polyline 
                        fill="none" 
                        stroke="#007bff" 
                        stroke-width="2"
                        points="${this.generateLinePoints(data)}"
                    />
                    ${data.map((item, index) => `
                        <circle 
                            cx="${(index / (data.length - 1)) * 360 + 20}" 
                            cy="${200 - (item.value / Math.max(...data.map(d => d.value))) * 160 - 20}"
                            r="4" 
                            fill="#007bff"
                            class="line-point"
                            data-index="${index}"
                        />
                    `).join('')}
                </svg>
                <div class="line-labels">
                    ${data.map(item => `<span class="line-label">${item.label}</span>`).join('')}
                </div>
            </div>
        `;
    }

    generatePieChart(data) {
        const total = data.reduce((sum, item) => sum + item.value, 0);
        let currentAngle = 0;
        
        return `
            <div class="pie-chart">
                <svg viewBox="0 0 200 200" class="pie-chart-svg">
                    ${data.map((item, index) => {
                        const angle = (item.value / total) * 360;
                        const x1 = 100 + 80 * Math.cos((currentAngle - 90) * Math.PI / 180);
                        const y1 = 100 + 80 * Math.sin((currentAngle - 90) * Math.PI / 180);
                        const x2 = 100 + 80 * Math.cos((currentAngle + angle - 90) * Math.PI / 180);
                        const y2 = 100 + 80 * Math.sin((currentAngle + angle - 90) * Math.PI / 180);
                        const largeArc = angle > 180 ? 1 : 0;
                        
                        const path = `M 100 100 L ${x1} ${y1} A 80 80 0 ${largeArc} 1 ${x2} ${y2} Z`;
                        currentAngle += angle;
                        
                        return `
                            <path 
                                d="${path}" 
                                fill="${this.getColor(index)}"
                                class="pie-slice"
                                data-index="${index}"
                            />
                        `;
                    }).join('')}
                </svg>
            </div>
        `;
    }

    generateLinePoints(data) {
        const maxValue = Math.max(...data.map(item => item.value));
        return data.map((item, index) => {
            const x = (index / (data.length - 1)) * 360 + 20;
            const y = 200 - (item.value / maxValue) * 160 - 20;
            return `${x},${y}`;
        }).join(' ');
    }

    getColor(index) {
        const colors = ['#007bff', '#28a745', '#ffc107', '#dc3545', '#6f42c1', '#20c997', '#fd7e14'];
        return colors[index % colors.length];
    }

    attachChartEvents() {
        if (!this.options.drillDown) return;

        // Add click events for drill-down
        this.container.addEventListener('click', (e) => {
            const drillTarget = e.target.closest('[data-drill="true"]');
            if (drillTarget) {
                const index = parseInt(drillTarget.dataset.index);
                this.drillDown(index);
            }
        });
    }

    drillDown(index) {
        const item = this.currentData[index];
        if (!item.drillData) return;

        // Add to drill stack
        this.drillStack.push({
            data: this.currentData,
            level: this.currentLevel,
            title: item.label
        });

        this.currentLevel++;
        this.renderChart(item.drillData);
        this.updateBreadcrumb(item.label);
        
        // Show back button
        document.getElementById('chart-back').style.display = 'inline-block';
    }

    navigateBack() {
        if (this.drillStack.length === 0) return;

        const previous = this.drillStack.pop();
        this.currentLevel = previous.level;
        this.renderChart(previous.data);
        this.updateBreadcrumb();

        if (this.drillStack.length === 0) {
            document.getElementById('chart-back').style.display = 'none';
        }
    }

    updateBreadcrumb(newLevel = null) {
        const breadcrumb = document.getElementById('chart-breadcrumb');
        
        if (newLevel) {
            breadcrumb.innerHTML += ` <i class="fas fa-chevron-right"></i> <span class="breadcrumb-item active">${newLevel}</span>`;
        } else {
            // Rebuild breadcrumb from stack
            let breadcrumbHTML = '<span class="breadcrumb-item active">Overview</span>';
            this.drillStack.forEach(level => {
                breadcrumbHTML += ` <i class="fas fa-chevron-right"></i> <span class="breadcrumb-item">${level.title}</span>`;
            });
            breadcrumb.innerHTML = breadcrumbHTML;
        }
    }

    exportChart() {
        // Implement chart export functionality
        const canvas = document.getElementById('chart-canvas');
        
        // Create a temporary canvas for export
        const exportCanvas = document.createElement('canvas');
        exportCanvas.width = 800;
        exportCanvas.height = 600;
        
        // Export as image (implementation would depend on chart library)
        const link = document.createElement('a');
        link.download = 'chart-export.png';
        link.href = exportCanvas.toDataURL();
        link.click();
    }
}

// Make classes globally available
window.LoadingStates = LoadingStates;
window.ErrorHandler = ErrorHandler;
window.AdvancedSearch = AdvancedSearch;
window.InteractiveCharts = InteractiveCharts; 