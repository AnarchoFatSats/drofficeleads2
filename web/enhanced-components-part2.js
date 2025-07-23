/*!
 * Enhanced CRM Components Part 2 - Advanced Features
 * Report Builder, Export, Dashboard Customization, Rich Text Editor, Calendar, File Upload, Bulk Actions
 */

// ====================================
// 5. CUSTOM REPORT BUILDER
// ====================================

class ReportBuilder {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            fields: [],
            aggregations: ['count', 'sum', 'avg', 'min', 'max'],
            groupBy: [],
            ...options
        };
        this.reportConfig = {
            fields: [],
            filters: [],
            groupBy: [],
            aggregations: [],
            sorting: []
        };
        this.init();
    }

    init() {
        this.render();
        this.attachEvents();
    }

    render() {
        this.container.innerHTML = `
            <div class="report-builder">
                <div class="report-builder-header">
                    <h3>Custom Report Builder</h3>
                    <div class="report-actions">
                        <button class="btn btn-secondary" id="save-report">Save Report</button>
                        <button class="btn btn-primary" id="generate-report">Generate Report</button>
                    </div>
                </div>

                <div class="report-builder-content">
                    <div class="report-section">
                        <h4>Select Fields</h4>
                        <div class="field-selector" id="field-selector">
                            ${this.renderFieldSelector()}
                        </div>
                    </div>

                    <div class="report-section">
                        <h4>Filters</h4>
                        <div class="filter-builder" id="filter-builder">
                            <button class="btn btn-outline-primary btn-sm" id="add-filter">
                                <i class="fas fa-plus"></i> Add Filter
                            </button>
                        </div>
                    </div>

                    <div class="report-section">
                        <h4>Group By</h4>
                        <div class="group-by-selector" id="group-by-selector">
                            ${this.renderGroupBySelector()}
                        </div>
                    </div>

                    <div class="report-section">
                        <h4>Aggregations</h4>
                        <div class="aggregation-builder" id="aggregation-builder">
                            <button class="btn btn-outline-primary btn-sm" id="add-aggregation">
                                <i class="fas fa-plus"></i> Add Aggregation
                            </button>
                        </div>
                    </div>

                    <div class="report-section">
                        <h4>Sorting</h4>
                        <div class="sorting-builder" id="sorting-builder">
                            <button class="btn btn-outline-primary btn-sm" id="add-sorting">
                                <i class="fas fa-plus"></i> Add Sorting
                            </button>
                        </div>
                    </div>
                </div>

                <div class="report-preview" id="report-preview" style="display: none;">
                    <h4>Report Preview</h4>
                    <div class="preview-content"></div>
                </div>
            </div>
        `;
    }

    renderFieldSelector() {
        return `
            <div class="field-grid">
                ${this.options.fields.map(field => `
                    <label class="field-checkbox-label">
                        <input type="checkbox" class="field-checkbox" value="${field.value}" data-type="${field.type}">
                        <span class="field-name">${field.label}</span>
                    </label>
                `).join('')}
            </div>
        `;
    }

    renderGroupBySelector() {
        return `
            <select class="form-select" id="group-by-field">
                <option value="">Select field to group by</option>
                ${this.options.fields.filter(field => field.groupable).map(field => 
                    `<option value="${field.value}">${field.label}</option>`
                ).join('')}
            </select>
        `;
    }

    attachEvents() {
        // Add filter
        document.getElementById('add-filter').addEventListener('click', () => {
            this.addFilterRow();
        });

        // Add aggregation
        document.getElementById('add-aggregation').addEventListener('click', () => {
            this.addAggregationRow();
        });

        // Add sorting
        document.getElementById('add-sorting').addEventListener('click', () => {
            this.addSortingRow();
        });

        // Generate report
        document.getElementById('generate-report').addEventListener('click', () => {
            this.generateReport();
        });

        // Save report
        document.getElementById('save-report').addEventListener('click', () => {
            this.saveReport();
        });
    }

    addFilterRow() {
        const filterBuilder = document.getElementById('filter-builder');
        const filterId = `filter-${Date.now()}`;
        
        const filterRow = document.createElement('div');
        filterRow.className = 'filter-row';
        filterRow.innerHTML = `
            <select class="form-select filter-field">
                <option value="">Select field</option>
                ${this.options.fields.map(field => 
                    `<option value="${field.value}" data-type="${field.type}">${field.label}</option>`
                ).join('')}
            </select>
            <select class="form-select filter-operator">
                <option value="equals">Equals</option>
                <option value="not_equals">Not Equals</option>
                <option value="contains">Contains</option>
                <option value="greater_than">Greater Than</option>
                <option value="less_than">Less Than</option>
            </select>
            <input type="text" class="form-control filter-value" placeholder="Value">
            <button class="btn btn-outline-danger btn-sm remove-filter">
                <i class="fas fa-times"></i>
            </button>
        `;

        filterBuilder.appendChild(filterRow);

        // Add remove functionality
        filterRow.querySelector('.remove-filter').addEventListener('click', () => {
            filterRow.remove();
        });
    }

    addAggregationRow() {
        const aggregationBuilder = document.getElementById('aggregation-builder');
        
        const aggregationRow = document.createElement('div');
        aggregationRow.className = 'aggregation-row';
        aggregationRow.innerHTML = `
            <select class="form-select aggregation-field">
                <option value="">Select field</option>
                ${this.options.fields.filter(field => field.aggregatable).map(field => 
                    `<option value="${field.value}">${field.label}</option>`
                ).join('')}
            </select>
            <select class="form-select aggregation-function">
                ${this.options.aggregations.map(agg => 
                    `<option value="${agg}">${agg.toUpperCase()}</option>`
                ).join('')}
            </select>
            <input type="text" class="form-control aggregation-alias" placeholder="Alias (optional)">
            <button class="btn btn-outline-danger btn-sm remove-aggregation">
                <i class="fas fa-times"></i>
            </button>
        `;

        aggregationBuilder.appendChild(aggregationRow);

        // Add remove functionality
        aggregationRow.querySelector('.remove-aggregation').addEventListener('click', () => {
            aggregationRow.remove();
        });
    }

    addSortingRow() {
        const sortingBuilder = document.getElementById('sorting-builder');
        
        const sortingRow = document.createElement('div');
        sortingRow.className = 'sorting-row';
        sortingRow.innerHTML = `
            <select class="form-select sorting-field">
                <option value="">Select field</option>
                ${this.options.fields.map(field => 
                    `<option value="${field.value}">${field.label}</option>`
                ).join('')}
            </select>
            <select class="form-select sorting-direction">
                <option value="asc">Ascending</option>
                <option value="desc">Descending</option>
            </select>
            <button class="btn btn-outline-danger btn-sm remove-sorting">
                <i class="fas fa-times"></i>
            </button>
        `;

        sortingBuilder.appendChild(sortingRow);

        // Add remove functionality
        sortingRow.querySelector('.remove-sorting').addEventListener('click', () => {
            sortingRow.remove();
        });
    }

    generateReport() {
        const reportConfig = this.buildReportConfig();
        
        // Show loading
        LoadingStates.showLoading('report-preview', 'table');
        document.getElementById('report-preview').style.display = 'block';

        // Simulate report generation
        setTimeout(() => {
            this.displayReportPreview(reportConfig);
            LoadingStates.hideLoading('report-preview');
        }, 1000);
    }

    buildReportConfig() {
        // Get selected fields
        const fields = Array.from(document.querySelectorAll('.field-checkbox:checked'))
            .map(cb => cb.value);

        // Get filters
        const filters = Array.from(document.querySelectorAll('.filter-row')).map(row => ({
            field: row.querySelector('.filter-field').value,
            operator: row.querySelector('.filter-operator').value,
            value: row.querySelector('.filter-value').value
        })).filter(filter => filter.field && filter.value);

        // Get group by
        const groupBy = document.getElementById('group-by-field').value;

        // Get aggregations
        const aggregations = Array.from(document.querySelectorAll('.aggregation-row')).map(row => ({
            field: row.querySelector('.aggregation-field').value,
            function: row.querySelector('.aggregation-function').value,
            alias: row.querySelector('.aggregation-alias').value
        })).filter(agg => agg.field && agg.function);

        // Get sorting
        const sorting = Array.from(document.querySelectorAll('.sorting-row')).map(row => ({
            field: row.querySelector('.sorting-field').value,
            direction: row.querySelector('.sorting-direction').value
        })).filter(sort => sort.field);

        return { fields, filters, groupBy, aggregations, sorting };
    }

    displayReportPreview(config) {
        const previewContent = document.querySelector('.preview-content');
        
        // Generate sample data for preview
        const sampleData = this.generateSampleData(config);
        
        previewContent.innerHTML = `
            <div class="report-summary">
                <div class="summary-item">
                    <strong>Fields:</strong> ${config.fields.join(', ') || 'All'}
                </div>
                <div class="summary-item">
                    <strong>Filters:</strong> ${config.filters.length} applied
                </div>
                <div class="summary-item">
                    <strong>Records:</strong> ${sampleData.length}
                </div>
            </div>
            <div class="report-table">
                ${this.generateReportTable(sampleData, config)}
            </div>
        `;
    }

    generateReportTable(data, config) {
        if (!data.length) return '<p>No data available</p>';

        const headers = config.fields.length ? config.fields : Object.keys(data[0]);
        
        return `
            <table class="table table-striped">
                <thead>
                    <tr>
                        ${headers.map(header => `<th>${header}</th>`).join('')}
                    </tr>
                </thead>
                <tbody>
                    ${data.slice(0, 10).map(row => `
                        <tr>
                            ${headers.map(header => `<td>${row[header] || '-'}</td>`).join('')}
                        </tr>
                    `).join('')}
                </tbody>
            </table>
            ${data.length > 10 ? `<p class="text-muted">Showing 10 of ${data.length} records</p>` : ''}
        `;
    }

    generateSampleData(config) {
        // Generate sample data based on config
        return Array.from({ length: 25 }, (_, i) => ({
            id: i + 1,
            practice_name: `Practice ${i + 1}`,
            owner_name: `Dr. Smith ${i + 1}`,
            city: ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix'][i % 5],
            state: ['NY', 'CA', 'IL', 'TX', 'AZ'][i % 5],
            score: Math.floor(Math.random() * 100),
            status: ['New', 'Contacted', 'Qualified', 'Proposal', 'Closed'][i % 5]
        }));
    }

    saveReport() {
        const reportConfig = this.buildReportConfig();
        const reportName = prompt('Enter a name for this report:');
        
        if (reportName) {
            // Save to localStorage for demo purposes
            const savedReports = JSON.parse(localStorage.getItem('savedReports') || '[]');
            savedReports.push({
                name: reportName,
                config: reportConfig,
                created: new Date().toISOString()
            });
            localStorage.setItem('savedReports', JSON.stringify(savedReports));
            
            ErrorHandler.showError(`Report "${reportName}" saved successfully!`, 'success');
        }
    }
}

// ====================================
// 6. EXPORT FUNCTIONALITY
// ====================================

class ExportManager {
    constructor() {
        this.exportTypes = ['csv', 'excel', 'pdf'];
    }

    createExportButton(containerId, data, options = {}) {
        const container = document.getElementById(containerId);
        const exportButton = document.createElement('div');
        exportButton.className = 'export-dropdown dropdown';
        exportButton.innerHTML = `
            <button class="btn btn-outline-primary dropdown-toggle" type="button" data-bs-toggle="dropdown">
                <i class="fas fa-download"></i> Export
            </button>
            <ul class="dropdown-menu">
                <li><a class="dropdown-item" href="#" data-type="csv">
                    <i class="fas fa-file-csv"></i> Export as CSV
                </a></li>
                <li><a class="dropdown-item" href="#" data-type="excel">
                    <i class="fas fa-file-excel"></i> Export as Excel
                </a></li>
                <li><a class="dropdown-item" href="#" data-type="pdf">
                    <i class="fas fa-file-pdf"></i> Export as PDF
                </a></li>
            </ul>
        `;

        // Add event listeners
        exportButton.addEventListener('click', (e) => {
            const exportType = e.target.dataset.type;
            if (exportType) {
                this.exportData(data, exportType, options);
            }
        });

        container.appendChild(exportButton);
        return exportButton;
    }

    exportData(data, type, options = {}) {
        const filename = options.filename || `export_${new Date().toISOString().split('T')[0]}`;
        
        switch (type) {
            case 'csv':
                this.exportCSV(data, filename);
                break;
            case 'excel':
                this.exportExcel(data, filename);
                break;
            case 'pdf':
                this.exportPDF(data, filename, options);
                break;
        }
    }

    exportCSV(data, filename) {
        if (!data.length) return;

        const headers = Object.keys(data[0]);
        const csvContent = [
            headers.join(','),
            ...data.map(row => headers.map(header => 
                `"${(row[header] || '').toString().replace(/"/g, '""')}"`
            ).join(','))
        ].join('\n');

        this.downloadFile(csvContent, `${filename}.csv`, 'text/csv');
    }

    exportExcel(data, filename) {
        // Simple Excel export using HTML table format
        if (!data.length) return;

        const headers = Object.keys(data[0]);
        const excelContent = `
            <table>
                <thead>
                    <tr>${headers.map(h => `<th>${h}</th>`).join('')}</tr>
                </thead>
                <tbody>
                    ${data.map(row => 
                        `<tr>${headers.map(h => `<td>${row[h] || ''}</td>`).join('')}</tr>`
                    ).join('')}
                </tbody>
            </table>
        `;

        this.downloadFile(excelContent, `${filename}.xls`, 'application/vnd.ms-excel');
    }

    exportPDF(data, filename, options = {}) {
        // Create a printable HTML version for PDF export
        const printWindow = window.open('', '_blank');
        const headers = Object.keys(data[0]);
        
        printWindow.document.write(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>${options.title || 'Export Report'}</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                    th { background-color: #f2f2f2; font-weight: bold; }
                    .header { margin-bottom: 20px; }
                    .export-date { color: #666; font-size: 12px; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>${options.title || 'Export Report'}</h1>
                    <div class="export-date">Generated on: ${new Date().toLocaleString()}</div>
                </div>
                <table>
                    <thead>
                        <tr>${headers.map(h => `<th>${h}</th>`).join('')}</tr>
                    </thead>
                    <tbody>
                        ${data.map(row => 
                            `<tr>${headers.map(h => `<td>${row[h] || ''}</td>`).join('')}</tr>`
                        ).join('')}
                    </tbody>
                </table>
            </body>
            </html>
        `);
        
        printWindow.document.close();
        setTimeout(() => {
            printWindow.print();
        }, 500);
    }

    downloadFile(content, filename, mimeType) {
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }
}

// ====================================
// 7. DASHBOARD CUSTOMIZATION
// ====================================

class DashboardCustomizer {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            widgets: [],
            layouts: ['one-column', 'two-column', 'three-column', 'two-one-grid'],
            ...options
        };
        this.currentLayout = 'two-column';
        this.widgets = [];
        this.init();
    }

    init() {
        this.render();
        this.attachEvents();
        this.loadDashboardState();
    }

    render() {
        this.container.innerHTML = `
            <div class="dashboard-customizer">
                <div class="customizer-header">
                    <div class="layout-selector">
                        <label>Layout:</label>
                        <select class="form-select" id="layout-selector">
                            ${this.options.layouts.map(layout => 
                                `<option value="${layout}">${this.formatLayoutName(layout)}</option>`
                            ).join('')}
                        </select>
                    </div>
                    <div class="customizer-actions">
                        <button class="btn btn-outline-secondary" id="edit-mode-toggle">
                            <i class="fas fa-edit"></i> Edit Mode
                        </button>
                        <button class="btn btn-outline-primary" id="add-widget">
                            <i class="fas fa-plus"></i> Add Widget
                        </button>
                        <button class="btn btn-primary" id="save-dashboard">
                            <i class="fas fa-save"></i> Save
                        </button>
                    </div>
                </div>

                <div class="dashboard-canvas" id="dashboard-canvas">
                    ${this.renderDashboardLayout()}
                </div>

                <div class="widget-panel" id="widget-panel" style="display: none;">
                    <h4>Available Widgets</h4>
                    <div class="widget-grid">
                        ${this.renderAvailableWidgets()}
                    </div>
                </div>
            </div>
        `;
    }

    renderDashboardLayout() {
        const layouts = {
            'one-column': '<div class="dashboard-column full-width" data-column="1"></div>',
            'two-column': `
                <div class="dashboard-column half-width" data-column="1"></div>
                <div class="dashboard-column half-width" data-column="2"></div>
            `,
            'three-column': `
                <div class="dashboard-column third-width" data-column="1"></div>
                <div class="dashboard-column third-width" data-column="2"></div>
                <div class="dashboard-column third-width" data-column="3"></div>
            `,
            'two-one-grid': `
                <div class="dashboard-row">
                    <div class="dashboard-column half-width" data-column="1"></div>
                    <div class="dashboard-column half-width" data-column="2"></div>
                </div>
                <div class="dashboard-row">
                    <div class="dashboard-column full-width" data-column="3"></div>
                </div>
            `
        };

        return `<div class="dashboard-layout ${this.currentLayout}">${layouts[this.currentLayout]}</div>`;
    }

    renderAvailableWidgets() {
        return this.options.widgets.map(widget => `
            <div class="widget-item" data-widget-type="${widget.type}">
                <div class="widget-icon">
                    <i class="fas fa-${widget.icon}"></i>
                </div>
                <div class="widget-info">
                    <div class="widget-name">${widget.name}</div>
                    <div class="widget-description">${widget.description}</div>
                </div>
                <button class="btn btn-sm btn-primary add-widget-btn">Add</button>
            </div>
        `).join('');
    }

    formatLayoutName(layout) {
        const nameMap = {
            'one-column': 'One Column',
            'two-column': 'Two Column',
            'three-column': 'Three Column',
            'two-one-grid': 'Two-One Grid'
        };
        return nameMap[layout] || layout.split('-').map(word => 
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
    }

    attachEvents() {
        // Layout selector
        document.getElementById('layout-selector').addEventListener('change', (e) => {
            this.changeLayout(e.target.value);
        });

        // Edit mode toggle
        document.getElementById('edit-mode-toggle').addEventListener('click', () => {
            this.toggleEditMode();
        });

        // Add widget panel toggle
        document.getElementById('add-widget').addEventListener('click', () => {
            this.toggleWidgetPanel();
        });

        // Save dashboard
        document.getElementById('save-dashboard').addEventListener('click', () => {
            this.saveDashboard();
        });

        // Widget panel events
        document.addEventListener('click', (e) => {
            if (e.target.matches('.add-widget-btn')) {
                const widgetType = e.target.closest('.widget-item').dataset.widgetType;
                this.addWidget(widgetType);
            }
        });
    }

    changeLayout(newLayout) {
        this.currentLayout = newLayout;
        const canvas = document.getElementById('dashboard-canvas');
        canvas.innerHTML = this.renderDashboardLayout();
        this.redistributeWidgets();
    }

    toggleEditMode() {
        const canvas = document.getElementById('dashboard-canvas');
        const editButton = document.getElementById('edit-mode-toggle');
        
        canvas.classList.toggle('edit-mode');
        
        if (canvas.classList.contains('edit-mode')) {
            editButton.innerHTML = '<i class="fas fa-check"></i> Done';
            this.enableDragAndDrop();
        } else {
            editButton.innerHTML = '<i class="fas fa-edit"></i> Edit Mode';
            this.disableDragAndDrop();
        }
    }

    toggleWidgetPanel() {
        const panel = document.getElementById('widget-panel');
        panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
    }

    addWidget(widgetType) {
        const widgetConfig = this.options.widgets.find(w => w.type === widgetType);
        if (!widgetConfig) return;

        const widgetId = `widget-${Date.now()}`;
        const widget = {
            id: widgetId,
            type: widgetType,
            config: widgetConfig,
            column: 1,
            order: this.widgets.length
        };

        this.widgets.push(widget);
        this.renderWidget(widget);
    }

    renderWidget(widget) {
        const column = document.querySelector(`[data-column="${widget.column}"]`);
        if (!column) return;

        const widgetElement = document.createElement('div');
        widgetElement.className = 'dashboard-widget';
        widgetElement.dataset.widgetId = widget.id;
        widgetElement.innerHTML = `
            <div class="widget-header">
                <h5 class="widget-title">${widget.config.name}</h5>
                <div class="widget-controls">
                    <button class="btn btn-sm btn-outline-secondary widget-settings">
                        <i class="fas fa-cog"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger widget-remove">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
            <div class="widget-content">
                ${this.generateWidgetContent(widget)}
            </div>
        `;

        // Add event listeners
        widgetElement.querySelector('.widget-remove').addEventListener('click', () => {
            this.removeWidget(widget.id);
        });

        column.appendChild(widgetElement);
    }

    generateWidgetContent(widget) {
        // Generate content based on widget type
        switch (widget.type) {
            case 'chart':
                return '<div class="chart-placeholder">Chart Widget</div>';
            case 'stats':
                return '<div class="stats-placeholder">Statistics Widget</div>';
            case 'table':
                return '<div class="table-placeholder">Table Widget</div>';
            case 'progress':
                return '<div class="progress-placeholder">Progress Widget</div>';
            default:
                return '<div class="default-placeholder">Widget Content</div>';
        }
    }

    removeWidget(widgetId) {
        this.widgets = this.widgets.filter(w => w.id !== widgetId);
        const widgetElement = document.querySelector(`[data-widget-id="${widgetId}"]`);
        if (widgetElement) {
            widgetElement.remove();
        }
    }

    redistributeWidgets() {
        // Redistribute widgets across new layout
        const columns = document.querySelectorAll('[data-column]');
        columns.forEach(column => column.innerHTML = '');

        this.widgets.forEach((widget, index) => {
            const columnIndex = (index % columns.length) + 1;
            widget.column = columnIndex;
            this.renderWidget(widget);
        });
    }

    enableDragAndDrop() {
        // Enable drag and drop for widgets (simplified implementation)
        const widgets = document.querySelectorAll('.dashboard-widget');
        widgets.forEach(widget => {
            widget.draggable = true;
            widget.addEventListener('dragstart', this.handleDragStart.bind(this));
            widget.addEventListener('dragend', this.handleDragEnd.bind(this));
        });

        const columns = document.querySelectorAll('[data-column]');
        columns.forEach(column => {
            column.addEventListener('dragover', this.handleDragOver.bind(this));
            column.addEventListener('drop', this.handleDrop.bind(this));
        });
    }

    disableDragAndDrop() {
        const widgets = document.querySelectorAll('.dashboard-widget');
        widgets.forEach(widget => {
            widget.draggable = false;
        });
    }

    handleDragStart(e) {
        e.dataTransfer.setData('text/plain', e.target.dataset.widgetId);
        e.target.classList.add('dragging');
    }

    handleDragEnd(e) {
        e.target.classList.remove('dragging');
    }

    handleDragOver(e) {
        e.preventDefault();
    }

    handleDrop(e) {
        e.preventDefault();
        const widgetId = e.dataTransfer.getData('text/plain');
        const targetColumn = e.target.closest('[data-column]');
        const widget = this.widgets.find(w => w.id === widgetId);
        
        if (widget && targetColumn) {
            widget.column = parseInt(targetColumn.dataset.column);
            const widgetElement = document.querySelector(`[data-widget-id="${widgetId}"]`);
            targetColumn.appendChild(widgetElement);
        }
    }

    saveDashboard() {
        const dashboardState = {
            layout: this.currentLayout,
            widgets: this.widgets
        };

        localStorage.setItem('dashboardState', JSON.stringify(dashboardState));
        ErrorHandler.showError('Dashboard saved successfully!', 'success');
    }

    loadDashboardState() {
        const savedState = localStorage.getItem('dashboardState');
        if (savedState) {
            const state = JSON.parse(savedState);
            this.currentLayout = state.layout;
            this.widgets = state.widgets || [];
            
            // Update layout selector
            document.getElementById('layout-selector').value = this.currentLayout;
            
            // Render saved widgets
            this.widgets.forEach(widget => {
                this.renderWidget(widget);
            });
        }
    }
}

// Make classes globally available
window.ReportBuilder = ReportBuilder;
window.ExportManager = ExportManager;
window.DashboardCustomizer = DashboardCustomizer; 