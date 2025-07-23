/*!
 * Enhanced CRM Components Part 3 - Final Features
 * Rich Text Editor, Calendar Integration, File Upload, Bulk Actions
 */

// ====================================
// 8. RICH TEXT EDITOR
// ====================================

class RichTextEditor {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            placeholder: 'Start typing...',
            toolbar: ['bold', 'italic', 'underline', 'link', 'list', 'image'],
            autosave: true,
            ...options
        };
        this.content = '';
        this.init();
    }

    init() {
        this.render();
        this.attachEvents();
    }

    render() {
        this.container.innerHTML = `
            <div class="rich-text-editor">
                <div class="editor-toolbar" id="editor-toolbar">
                    ${this.renderToolbar()}
                </div>
                <div class="editor-content" 
                     contenteditable="true" 
                     id="editor-content"
                     data-placeholder="${this.options.placeholder}">
                </div>
                <div class="editor-footer">
                    <div class="editor-stats">
                        <span id="char-count">0 characters</span>
                        <span id="word-count">0 words</span>
                    </div>
                    <div class="editor-actions">
                        <button class="btn btn-sm btn-outline-secondary" id="clear-editor">Clear</button>
                        <button class="btn btn-sm btn-primary" id="save-content">Save</button>
                    </div>
                </div>
            </div>
        `;
    }

    renderToolbar() {
        const tools = {
            bold: '<button class="editor-btn" data-command="bold"><i class="fas fa-bold"></i></button>',
            italic: '<button class="editor-btn" data-command="italic"><i class="fas fa-italic"></i></button>',
            underline: '<button class="editor-btn" data-command="underline"><i class="fas fa-underline"></i></button>',
            link: '<button class="editor-btn" data-command="createLink"><i class="fas fa-link"></i></button>',
            list: '<button class="editor-btn" data-command="insertUnorderedList"><i class="fas fa-list-ul"></i></button>',
            image: '<button class="editor-btn" data-command="insertImage"><i class="fas fa-image"></i></button>',
            fontSize: `
                <select class="editor-select" data-command="fontSize">
                    <option value="3">12px</option>
                    <option value="4" selected>14px</option>
                    <option value="5">16px</option>
                    <option value="6">18px</option>
                    <option value="7">24px</option>
                </select>
            `,
            foreColor: '<input type="color" class="editor-color" data-command="foreColor" title="Text Color">',
            backColor: '<input type="color" class="editor-color" data-command="backColor" title="Background Color">'
        };

        return this.options.toolbar.map(tool => tools[tool] || '').join('');
    }

    attachEvents() {
        const toolbar = document.getElementById('editor-toolbar');
        const content = document.getElementById('editor-content');

        // Toolbar events
        toolbar.addEventListener('click', (e) => {
            if (e.target.matches('.editor-btn')) {
                e.preventDefault();
                const command = e.target.dataset.command;
                this.executeCommand(command);
            }
        });

        toolbar.addEventListener('change', (e) => {
            if (e.target.matches('.editor-select, .editor-color')) {
                const command = e.target.dataset.command;
                const value = e.target.value;
                this.executeCommand(command, value);
            }
        });

        // Content events
        content.addEventListener('input', () => {
            this.updateStats();
            if (this.options.autosave) {
                this.autosave();
            }
        });

        content.addEventListener('paste', (e) => {
            e.preventDefault();
            const text = e.clipboardData.getData('text/plain');
            document.execCommand('insertText', false, text);
        });

        // Action buttons
        document.getElementById('clear-editor').addEventListener('click', () => {
            this.clearContent();
        });

        document.getElementById('save-content').addEventListener('click', () => {
            this.saveContent();
        });

        // Initialize stats
        this.updateStats();
    }

    executeCommand(command, value = null) {
        const content = document.getElementById('editor-content');
        content.focus();

        if (command === 'createLink') {
            const url = prompt('Enter URL:');
            if (url) {
                document.execCommand(command, false, url);
            }
        } else if (command === 'insertImage') {
            const url = prompt('Enter image URL:');
            if (url) {
                document.execCommand(command, false, url);
            }
        } else {
            document.execCommand(command, false, value);
        }

        this.updateStats();
    }

    updateStats() {
        const content = document.getElementById('editor-content');
        const text = content.textContent || content.innerText || '';
        const charCount = text.length;
        const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;

        document.getElementById('char-count').textContent = `${charCount} characters`;
        document.getElementById('word-count').textContent = `${wordCount} words`;
    }

    clearContent() {
        if (confirm('Are you sure you want to clear all content?')) {
            document.getElementById('editor-content').innerHTML = '';
            this.updateStats();
        }
    }

    saveContent() {
        const content = document.getElementById('editor-content').innerHTML;
        this.content = content;
        
        // Trigger save event
        const saveEvent = new CustomEvent('contentSaved', {
            detail: { content }
        });
        this.container.dispatchEvent(saveEvent);
        
        ErrorHandler.showError('Content saved successfully!', 'success');
    }

    autosave() {
        clearTimeout(this.autosaveTimeout);
        this.autosaveTimeout = setTimeout(() => {
            const content = document.getElementById('editor-content').innerHTML;
            localStorage.setItem(`editor_autosave_${this.container.id}`, content);
        }, 2000);
    }

    getContent() {
        return document.getElementById('editor-content').innerHTML;
    }

    setContent(content) {
        document.getElementById('editor-content').innerHTML = content;
        this.updateStats();
    }
}

// ====================================
// 9. CALENDAR INTEGRATION
// ====================================

class CalendarIntegration {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            view: 'month',
            editable: true,
            timeSlots: ['09:00', '10:00', '11:00', '12:00', '14:00', '15:00', '16:00', '17:00'],
            ...options
        };
        this.currentDate = new Date();
        this.events = [];
        this.init();
    }

    init() {
        this.render();
        this.attachEvents();
        this.loadEvents();
    }

    render() {
        this.container.innerHTML = `
            <div class="calendar-integration">
                <div class="calendar-header">
                    <div class="calendar-navigation">
                        <button class="btn btn-outline-secondary" id="prev-period">
                            <i class="fas fa-chevron-left"></i>
                        </button>
                        <h3 id="current-period">${this.formatPeriod()}</h3>
                        <button class="btn btn-outline-secondary" id="next-period">
                            <i class="fas fa-chevron-right"></i>
                        </button>
                    </div>
                    <div class="calendar-controls">
                        <div class="view-selector">
                            <button class="btn btn-sm btn-outline-primary ${this.options.view === 'day' ? 'active' : ''}" 
                                    data-view="day">Day</button>
                            <button class="btn btn-sm btn-outline-primary ${this.options.view === 'week' ? 'active' : ''}" 
                                    data-view="week">Week</button>
                            <button class="btn btn-sm btn-outline-primary ${this.options.view === 'month' ? 'active' : ''}" 
                                    data-view="month">Month</button>
                        </div>
                        <button class="btn btn-primary" id="add-appointment">
                            <i class="fas fa-plus"></i> Add Appointment
                        </button>
                    </div>
                </div>
                <div class="calendar-content" id="calendar-content">
                    ${this.renderCalendarView()}
                </div>
            </div>

            <!-- Appointment Modal -->
            <div class="modal fade" id="appointmentModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Schedule Appointment</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            ${this.renderAppointmentForm()}
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" id="save-appointment">Save</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderCalendarView() {
        switch (this.options.view) {
            case 'day':
                return this.renderDayView();
            case 'week':
                return this.renderWeekView();
            case 'month':
                return this.renderMonthView();
            default:
                return this.renderMonthView();
        }
    }

    renderDayView() {
        const date = this.currentDate;
        const dayEvents = this.getEventsForDate(date);

        return `
            <div class="day-view">
                <div class="time-slots">
                    ${this.options.timeSlots.map(time => `
                        <div class="time-slot" data-time="${time}">
                            <div class="time-label">${time}</div>
                            <div class="slot-content">
                                ${this.renderEventsForTimeSlot(date, time, dayEvents)}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    renderWeekView() {
        const startOfWeek = new Date(this.currentDate);
        startOfWeek.setDate(startOfWeek.getDate() - startOfWeek.getDay());

        const weekDays = Array.from({ length: 7 }, (_, i) => {
            const date = new Date(startOfWeek);
            date.setDate(date.getDate() + i);
            return date;
        });

        return `
            <div class="week-view">
                <div class="week-header">
                    ${weekDays.map(date => `
                        <div class="day-header">
                            <div class="day-name">${date.toLocaleDateString('en', { weekday: 'short' })}</div>
                            <div class="day-number">${date.getDate()}</div>
                        </div>
                    `).join('')}
                </div>
                <div class="week-content">
                    ${this.options.timeSlots.map(time => `
                        <div class="time-row">
                            <div class="time-label">${time}</div>
                            ${weekDays.map(date => `
                                <div class="day-slot" data-date="${date.toISOString().split('T')[0]}" data-time="${time}">
                                    ${this.renderEventsForTimeSlot(date, time, this.getEventsForDate(date))}
                                </div>
                            `).join('')}
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    renderMonthView() {
        const year = this.currentDate.getFullYear();
        const month = this.currentDate.getMonth();
        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);
        const startDate = new Date(firstDay);
        startDate.setDate(startDate.getDate() - firstDay.getDay());

        const weeks = [];
        const currentDate = new Date(startDate);
        
        while (currentDate <= lastDay || currentDate.getDay() !== 0) {
            const week = [];
            for (let i = 0; i < 7; i++) {
                week.push(new Date(currentDate));
                currentDate.setDate(currentDate.getDate() + 1);
            }
            weeks.push(week);
            if (currentDate.getMonth() !== month && currentDate.getDay() === 0) break;
        }

        return `
            <div class="month-view">
                <div class="month-header">
                    <div class="day-name">Sun</div>
                    <div class="day-name">Mon</div>
                    <div class="day-name">Tue</div>
                    <div class="day-name">Wed</div>
                    <div class="day-name">Thu</div>
                    <div class="day-name">Fri</div>
                    <div class="day-name">Sat</div>
                </div>
                <div class="month-content">
                    ${weeks.map(week => `
                        <div class="week-row">
                            ${week.map(date => `
                                <div class="month-day ${date.getMonth() !== month ? 'other-month' : ''}" 
                                     data-date="${date.toISOString().split('T')[0]}">
                                    <div class="day-number">${date.getDate()}</div>
                                    <div class="day-events">
                                        ${this.renderEventsForDate(date).slice(0, 3).map(event => `
                                            <div class="event-dot" style="background-color: ${event.color || '#007bff'}" 
                                                 title="${event.title}"></div>
                                        `).join('')}
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    renderAppointmentForm() {
        return `
            <form id="appointment-form">
                <div class="mb-3">
                    <label class="form-label">Title</label>
                    <input type="text" class="form-control" id="appointment-title" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Lead/Contact</label>
                    <select class="form-select" id="appointment-contact">
                        <option value="">Select a lead...</option>
                        <!-- Populated dynamically -->
                    </select>
                </div>
                <div class="row">
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label class="form-label">Date</label>
                            <input type="date" class="form-control" id="appointment-date" required>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label class="form-label">Time</label>
                            <input type="time" class="form-control" id="appointment-time" required>
                        </div>
                    </div>
                </div>
                <div class="mb-3">
                    <label class="form-label">Duration (minutes)</label>
                    <select class="form-select" id="appointment-duration">
                        <option value="30">30 minutes</option>
                        <option value="60" selected>1 hour</option>
                        <option value="90">1.5 hours</option>
                        <option value="120">2 hours</option>
                    </select>
                </div>
                <div class="mb-3">
                    <label class="form-label">Description</label>
                    <textarea class="form-control" id="appointment-description" rows="3"></textarea>
                </div>
                <div class="mb-3">
                    <label class="form-label">Color</label>
                    <div class="color-picker">
                        <input type="color" class="form-control form-control-color" id="appointment-color" value="#007bff">
                    </div>
                </div>
            </form>
        `;
    }

    renderEventsForTimeSlot(date, time, events) {
        const timeEvents = events.filter(event => {
            const eventTime = new Date(event.start).toTimeString().substring(0, 5);
            return eventTime === time;
        });

        return timeEvents.map(event => `
            <div class="calendar-event" style="background-color: ${event.color || '#007bff'}" 
                 data-event-id="${event.id}">
                <div class="event-title">${event.title}</div>
                <div class="event-time">${event.duration || 60}min</div>
            </div>
        `).join('');
    }

    renderEventsForDate(date) {
        const dateStr = date.toISOString().split('T')[0];
        return this.events.filter(event => 
            event.start.startsWith(dateStr)
        );
    }

    attachEvents() {
        // Navigation
        document.getElementById('prev-period').addEventListener('click', () => {
            this.navigatePeriod(-1);
        });

        document.getElementById('next-period').addEventListener('click', () => {
            this.navigatePeriod(1);
        });

        // View switching
        this.container.addEventListener('click', (e) => {
            if (e.target.matches('[data-view]')) {
                this.switchView(e.target.dataset.view);
            }
        });

        // Add appointment
        document.getElementById('add-appointment').addEventListener('click', () => {
            this.showAppointmentModal();
        });

        // Save appointment
        document.getElementById('save-appointment').addEventListener('click', () => {
            this.saveAppointment();
        });

        // Calendar interactions
        this.container.addEventListener('click', (e) => {
            if (e.target.matches('.day-slot, .month-day')) {
                const date = e.target.dataset.date;
                const time = e.target.dataset.time || '09:00';
                this.showAppointmentModal(date, time);
            }
        });
    }

    navigatePeriod(direction) {
        switch (this.options.view) {
            case 'day':
                this.currentDate.setDate(this.currentDate.getDate() + direction);
                break;
            case 'week':
                this.currentDate.setDate(this.currentDate.getDate() + (direction * 7));
                break;
            case 'month':
                this.currentDate.setMonth(this.currentDate.getMonth() + direction);
                break;
        }
        this.updateCalendar();
    }

    switchView(view) {
        this.options.view = view;
        
        // Update active button
        this.container.querySelectorAll('[data-view]').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.view === view);
        });
        
        this.updateCalendar();
    }

    updateCalendar() {
        document.getElementById('current-period').textContent = this.formatPeriod();
        document.getElementById('calendar-content').innerHTML = this.renderCalendarView();
    }

    formatPeriod() {
        switch (this.options.view) {
            case 'day':
                return this.currentDate.toLocaleDateString('en', { 
                    weekday: 'long', 
                    year: 'numeric', 
                    month: 'long', 
                    day: 'numeric' 
                });
            case 'week':
                const startOfWeek = new Date(this.currentDate);
                startOfWeek.setDate(startOfWeek.getDate() - startOfWeek.getDay());
                const endOfWeek = new Date(startOfWeek);
                endOfWeek.setDate(endOfWeek.getDate() + 6);
                return `${startOfWeek.toLocaleDateString()} - ${endOfWeek.toLocaleDateString()}`;
            case 'month':
                return this.currentDate.toLocaleDateString('en', { 
                    year: 'numeric', 
                    month: 'long' 
                });
        }
    }

    showAppointmentModal(date = null, time = null) {
        if (date) {
            document.getElementById('appointment-date').value = date;
        }
        if (time) {
            document.getElementById('appointment-time').value = time;
        }
        
        // Show modal (assuming Bootstrap is available)
        const modal = new bootstrap.Modal(document.getElementById('appointmentModal'));
        modal.show();
    }

    saveAppointment() {
        const form = document.getElementById('appointment-form');
        const formData = new FormData(form);
        
        const appointment = {
            id: Date.now().toString(),
            title: document.getElementById('appointment-title').value,
            contact: document.getElementById('appointment-contact').value,
            start: `${document.getElementById('appointment-date').value}T${document.getElementById('appointment-time').value}`,
            duration: parseInt(document.getElementById('appointment-duration').value),
            description: document.getElementById('appointment-description').value,
            color: document.getElementById('appointment-color').value
        };

        this.events.push(appointment);
        this.saveEvents();
        this.updateCalendar();
        
        // Hide modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('appointmentModal'));
        modal.hide();
        
        ErrorHandler.showError('Appointment scheduled successfully!', 'success');
    }

    getEventsForDate(date) {
        const dateStr = date.toISOString().split('T')[0];
        return this.events.filter(event => 
            event.start.startsWith(dateStr)
        );
    }

    saveEvents() {
        localStorage.setItem('calendarEvents', JSON.stringify(this.events));
    }

    loadEvents() {
        const savedEvents = localStorage.getItem('calendarEvents');
        if (savedEvents) {
            this.events = JSON.parse(savedEvents);
        }
    }
}

// ====================================
// 10. FILE UPLOAD SYSTEM
// ====================================

class FileUpload {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            maxFiles: 10,
            maxSize: 10 * 1024 * 1024, // 10MB
            allowedTypes: ['image/*', 'application/pdf', '.doc', '.docx', '.txt'],
            multiple: true,
            ...options
        };
        this.files = [];
        this.init();
    }

    init() {
        this.render();
        this.attachEvents();
    }

    render() {
        this.container.innerHTML = `
            <div class="file-upload">
                <div class="upload-area" id="upload-area">
                    <div class="upload-icon">
                        <i class="fas fa-cloud-upload-alt"></i>
                    </div>
                    <div class="upload-text">
                        <h4>Drop files here or click to browse</h4>
                        <p>Supported formats: Images, PDF, DOC, TXT (Max ${this.formatFileSize(this.options.maxSize)})</p>
                    </div>
                    <input type="file" 
                           id="file-input" 
                           class="file-input" 
                           ${this.options.multiple ? 'multiple' : ''} 
                           accept="${this.options.allowedTypes.join(',')}">
                </div>

                <div class="upload-progress" id="upload-progress" style="display: none;">
                    <div class="progress">
                        <div class="progress-bar" role="progressbar" style="width: 0%"></div>
                    </div>
                    <div class="progress-text">Uploading...</div>
                </div>

                <div class="file-list" id="file-list">
                    <!-- Uploaded files will appear here -->
                </div>
            </div>
        `;
    }

    attachEvents() {
        const uploadArea = document.getElementById('upload-area');
        const fileInput = document.getElementById('file-input');

        // Click to browse
        uploadArea.addEventListener('click', () => {
            fileInput.click();
        });

        // File selection
        fileInput.addEventListener('change', (e) => {
            this.handleFiles(Array.from(e.target.files));
        });

        // Drag and drop
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('drag-over');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('drag-over');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('drag-over');
            this.handleFiles(Array.from(e.dataTransfer.files));
        });
    }

    handleFiles(files) {
        // Validate files
        const validFiles = files.filter(file => this.validateFile(file));
        
        if (validFiles.length !== files.length) {
            ErrorHandler.showError('Some files were rejected due to size or type restrictions.', 'warning');
        }

        // Check max files limit
        if (this.files.length + validFiles.length > this.options.maxFiles) {
            ErrorHandler.showError(`Maximum ${this.options.maxFiles} files allowed.`, 'error');
            return;
        }

        // Process valid files
        validFiles.forEach(file => {
            this.addFile(file);
        });
    }

    validateFile(file) {
        // Check file size
        if (file.size > this.options.maxSize) {
            ErrorHandler.showError(`${file.name} is too large. Maximum size is ${this.formatFileSize(this.options.maxSize)}.`, 'error');
            return false;
        }

        // Check file type
        const isValidType = this.options.allowedTypes.some(type => {
            if (type.includes('*')) {
                return file.type.startsWith(type.replace('*', ''));
            } else if (type.startsWith('.')) {
                return file.name.toLowerCase().endsWith(type.toLowerCase());
            } else {
                return file.type === type;
            }
        });

        if (!isValidType) {
            ErrorHandler.showError(`${file.name} has an unsupported file type.`, 'error');
            return false;
        }

        return true;
    }

    addFile(file) {
        const fileObj = {
            id: Date.now() + Math.random(),
            file: file,
            name: file.name,
            size: file.size,
            type: file.type,
            status: 'pending',
            progress: 0
        };

        this.files.push(fileObj);
        this.renderFile(fileObj);
        this.uploadFile(fileObj);
    }

    renderFile(fileObj) {
        const fileList = document.getElementById('file-list');
        const fileElement = document.createElement('div');
        fileElement.className = 'file-item';
        fileElement.dataset.fileId = fileObj.id;
        fileElement.innerHTML = `
            <div class="file-info">
                <div class="file-icon">
                    <i class="fas fa-${this.getFileIcon(fileObj.type)}"></i>
                </div>
                <div class="file-details">
                    <div class="file-name">${fileObj.name}</div>
                    <div class="file-size">${this.formatFileSize(fileObj.size)}</div>
                </div>
            </div>
            <div class="file-progress">
                <div class="progress">
                    <div class="progress-bar" style="width: ${fileObj.progress}%"></div>
                </div>
                <div class="file-status">${fileObj.status}</div>
            </div>
            <div class="file-actions">
                <button class="btn btn-sm btn-outline-danger remove-file" data-file-id="${fileObj.id}">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        // Add remove functionality
        fileElement.querySelector('.remove-file').addEventListener('click', () => {
            this.removeFile(fileObj.id);
        });

        fileList.appendChild(fileElement);
    }

    uploadFile(fileObj) {
        // Simulate file upload
        fileObj.status = 'uploading';
        this.updateFileDisplay(fileObj);

        const uploadInterval = setInterval(() => {
            fileObj.progress += Math.random() * 20;
            
            if (fileObj.progress >= 100) {
                fileObj.progress = 100;
                fileObj.status = 'completed';
                clearInterval(uploadInterval);
                
                // Trigger upload complete event
                const uploadEvent = new CustomEvent('fileUploaded', {
                    detail: { file: fileObj }
                });
                this.container.dispatchEvent(uploadEvent);
            }
            
            this.updateFileDisplay(fileObj);
        }, 200);
    }

    updateFileDisplay(fileObj) {
        const fileElement = document.querySelector(`[data-file-id="${fileObj.id}"]`);
        if (fileElement) {
            const progressBar = fileElement.querySelector('.progress-bar');
            const statusElement = fileElement.querySelector('.file-status');
            
            progressBar.style.width = `${fileObj.progress}%`;
            statusElement.textContent = fileObj.status;
            
            // Add status classes
            fileElement.className = `file-item ${fileObj.status}`;
        }
    }

    removeFile(fileId) {
        this.files = this.files.filter(file => file.id !== fileId);
        const fileElement = document.querySelector(`[data-file-id="${fileId}"]`);
        if (fileElement) {
            fileElement.remove();
        }
    }

    getFileIcon(mimeType) {
        if (mimeType.startsWith('image/')) return 'image';
        if (mimeType === 'application/pdf') return 'file-pdf';
        if (mimeType.includes('word') || mimeType.includes('document')) return 'file-word';
        if (mimeType.includes('text')) return 'file-alt';
        return 'file';
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    getUploadedFiles() {
        return this.files.filter(file => file.status === 'completed');
    }

    clearFiles() {
        this.files = [];
        document.getElementById('file-list').innerHTML = '';
    }
}

// ====================================
// 11. BULK ACTIONS SYSTEM
// ====================================

class BulkActions {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            actions: [
                { id: 'delete', label: 'Delete Selected', icon: 'trash', class: 'btn-danger' },
                { id: 'export', label: 'Export Selected', icon: 'download', class: 'btn-primary' },
                { id: 'assign', label: 'Assign to Agent', icon: 'user-plus', class: 'btn-success' },
                { id: 'update-status', label: 'Update Status', icon: 'edit', class: 'btn-warning' }
            ],
            selectAllSelector: '.select-all',
            itemSelector: '.bulk-item',
            ...options
        };
        this.selectedItems = new Set();
        this.init();
    }

    init() {
        this.render();
        this.attachEvents();
    }

    render() {
        this.container.innerHTML = `
            <div class="bulk-actions">
                <div class="bulk-toolbar" id="bulk-toolbar" style="display: none;">
                    <div class="selection-info">
                        <span id="selection-count">0 items selected</span>
                        <button class="btn btn-sm btn-outline-secondary" id="clear-selection">Clear</button>
                    </div>
                    <div class="bulk-action-buttons">
                        ${this.options.actions.map(action => `
                            <button class="btn btn-sm ${action.class}" 
                                    data-action="${action.id}"
                                    title="${action.label}">
                                <i class="fas fa-${action.icon}"></i>
                                ${action.label}
                            </button>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    }

    attachEvents() {
        // Select all checkbox
        document.addEventListener('change', (e) => {
            if (e.target.matches(this.options.selectAllSelector)) {
                this.toggleSelectAll(e.target.checked);
            }
        });

        // Individual item checkboxes
        document.addEventListener('change', (e) => {
            if (e.target.matches(`${this.options.itemSelector} input[type="checkbox"]`)) {
                this.toggleItem(e.target.value, e.target.checked);
            }
        });

        // Bulk action buttons
        this.container.addEventListener('click', (e) => {
            if (e.target.matches('[data-action]')) {
                const action = e.target.dataset.action;
                this.executeAction(action);
            }
        });

        // Clear selection
        document.getElementById('clear-selection').addEventListener('click', () => {
            this.clearSelection();
        });
    }

    toggleSelectAll(checked) {
        const items = document.querySelectorAll(`${this.options.itemSelector} input[type="checkbox"]`);
        items.forEach(item => {
            item.checked = checked;
            this.toggleItem(item.value, checked);
        });
    }

    toggleItem(itemId, selected) {
        if (selected) {
            this.selectedItems.add(itemId);
        } else {
            this.selectedItems.delete(itemId);
        }
        
        this.updateDisplay();
    }

    updateDisplay() {
        const count = this.selectedItems.size;
        const toolbar = document.getElementById('bulk-toolbar');
        const countElement = document.getElementById('selection-count');
        
        if (count > 0) {
            toolbar.style.display = 'flex';
            countElement.textContent = `${count} item${count !== 1 ? 's' : ''} selected`;
        } else {
            toolbar.style.display = 'none';
        }

        // Update select all checkbox
        const selectAllCheckbox = document.querySelector(this.options.selectAllSelector);
        const allItems = document.querySelectorAll(`${this.options.itemSelector} input[type="checkbox"]`);
        
        if (selectAllCheckbox && allItems.length > 0) {
            const checkedItems = Array.from(allItems).filter(item => item.checked);
            selectAllCheckbox.indeterminate = checkedItems.length > 0 && checkedItems.length < allItems.length;
            selectAllCheckbox.checked = checkedItems.length === allItems.length;
        }
    }

    executeAction(actionId) {
        if (this.selectedItems.size === 0) {
            ErrorHandler.showError('No items selected.', 'warning');
            return;
        }

        const selectedArray = Array.from(this.selectedItems);
        
        switch (actionId) {
            case 'delete':
                this.confirmDelete(selectedArray);
                break;
            case 'export':
                this.exportSelected(selectedArray);
                break;
            case 'assign':
                this.showAssignModal(selectedArray);
                break;
            case 'update-status':
                this.showStatusModal(selectedArray);
                break;
            default:
                // Trigger custom action event
                const actionEvent = new CustomEvent('bulkAction', {
                    detail: { action: actionId, items: selectedArray }
                });
                this.container.dispatchEvent(actionEvent);
        }
    }

    confirmDelete(items) {
        const message = `Are you sure you want to delete ${items.length} item${items.length !== 1 ? 's' : ''}? This action cannot be undone.`;
        
        if (confirm(message)) {
            // Trigger delete event
            const deleteEvent = new CustomEvent('bulkDelete', {
                detail: { items }
            });
            this.container.dispatchEvent(deleteEvent);
            
            ErrorHandler.showError(`${items.length} item${items.length !== 1 ? 's' : ''} deleted successfully.`, 'success');
            this.clearSelection();
        }
    }

    exportSelected(items) {
        // Trigger export event
        const exportEvent = new CustomEvent('bulkExport', {
            detail: { items }
        });
        this.container.dispatchEvent(exportEvent);
        
        ErrorHandler.showError(`Exporting ${items.length} item${items.length !== 1 ? 's' : ''}...`, 'info');
    }

    showAssignModal(items) {
        // Create and show assign modal
        const modal = this.createModal('Assign to Agent', `
            <div class="mb-3">
                <label class="form-label">Select Agent</label>
                <select class="form-select" id="assign-agent">
                    <option value="">Choose an agent...</option>
                    <option value="agent1">Agent 1</option>
                    <option value="agent2">Agent 2</option>
                    <option value="agent3">Agent 3</option>
                </select>
            </div>
            <div class="mb-3">
                <label class="form-label">Note (optional)</label>
                <textarea class="form-control" id="assign-note" rows="3"></textarea>
            </div>
        `, () => {
            const agent = document.getElementById('assign-agent').value;
            const note = document.getElementById('assign-note').value;
            
            if (agent) {
                const assignEvent = new CustomEvent('bulkAssign', {
                    detail: { items, agent, note }
                });
                this.container.dispatchEvent(assignEvent);
                
                ErrorHandler.showError(`${items.length} item${items.length !== 1 ? 's' : ''} assigned to ${agent}.`, 'success');
                this.clearSelection();
                modal.hide();
            }
        });
    }

    showStatusModal(items) {
        // Create and show status modal
        const modal = this.createModal('Update Status', `
            <div class="mb-3">
                <label class="form-label">New Status</label>
                <select class="form-select" id="new-status">
                    <option value="">Choose status...</option>
                    <option value="new">New</option>
                    <option value="contacted">Contacted</option>
                    <option value="qualified">Qualified</option>
                    <option value="proposal">Proposal</option>
                    <option value="closed-won">Closed Won</option>
                    <option value="closed-lost">Closed Lost</option>
                </select>
            </div>
        `, () => {
            const status = document.getElementById('new-status').value;
            
            if (status) {
                const statusEvent = new CustomEvent('bulkStatusUpdate', {
                    detail: { items, status }
                });
                this.container.dispatchEvent(statusEvent);
                
                ErrorHandler.showError(`${items.length} item${items.length !== 1 ? 's' : ''} updated to ${status}.`, 'success');
                this.clearSelection();
                modal.hide();
            }
        });
    }

    createModal(title, content, onSave) {
        const modalId = `bulk-modal-${Date.now()}`;
        const modalHtml = `
            <div class="modal fade" id="${modalId}" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">${title}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            ${content}
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" id="modal-save">Save</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);
        const modalElement = document.getElementById(modalId);
        const modal = new bootstrap.Modal(modalElement);
        
        modalElement.querySelector('#modal-save').addEventListener('click', onSave);
        
        modalElement.addEventListener('hidden.bs.modal', () => {
            modalElement.remove();
        });
        
        modal.show();
        return modal;
    }

    clearSelection() {
        this.selectedItems.clear();
        
        // Uncheck all items
        document.querySelectorAll(`${this.options.itemSelector} input[type="checkbox"]`).forEach(item => {
            item.checked = false;
        });
        
        // Uncheck select all
        const selectAllCheckbox = document.querySelector(this.options.selectAllSelector);
        if (selectAllCheckbox) {
            selectAllCheckbox.checked = false;
            selectAllCheckbox.indeterminate = false;
        }
        
        this.updateDisplay();
    }

    getSelectedItems() {
        return Array.from(this.selectedItems);
    }
}

// Make classes globally available
window.RichTextEditor = RichTextEditor;
window.CalendarIntegration = CalendarIntegration;
window.FileUpload = FileUpload;
window.BulkActions = BulkActions; 