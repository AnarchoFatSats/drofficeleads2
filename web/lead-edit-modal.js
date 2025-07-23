/*!
 * Lead Edit Modal Component
 * Allows agents to edit core lead information with proper validation and API integration
 */

class LeadEditModal {
    constructor() {
        this.modal = null;
        this.currentLead = null;
        this.isDirty = false;
        this.init();
    }

    init() {
        this.createModal();
        this.setupEventListeners();
    }

    createModal() {
        // Create modal HTML structure
        const modalHTML = `
            <div class="modal fade" id="leadEditModal" tabindex="-1" aria-labelledby="leadEditModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header bg-primary text-white">
                            <h5 class="modal-title" id="leadEditModalLabel">
                                <i class="fas fa-edit"></i> Edit Lead Information
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <form id="leadEditForm">
                                <!-- Core Lead Information -->
                                <div class="section-header">
                                    <h6><i class="fas fa-building"></i> Practice Information</h6>
                                </div>
                                <div class="row mb-3">
                                    <div class="col-md-6">
                                        <label for="edit-practice-name" class="form-label">Practice Name</label>
                                        <input type="text" class="form-control" id="edit-practice-name" name="practice_name" required>
                                    </div>
                                    <div class="col-md-6">
                                        <label for="edit-owner-name" class="form-label">Owner Name</label>
                                        <input type="text" class="form-control" id="edit-owner-name" name="owner_name">
                                    </div>
                                </div>

                                <!-- Phone Numbers -->
                                <div class="section-header">
                                    <h6><i class="fas fa-phone"></i> Contact Information</h6>
                                </div>
                                <div class="row mb-3">
                                    <div class="col-md-6">
                                        <label for="edit-practice-phone" class="form-label">Practice Phone</label>
                                        <input type="tel" class="form-control" id="edit-practice-phone" name="practice_phone" 
                                               pattern="[0-9\-\(\)\+\s]*" placeholder="(555) 123-4567">
                                    </div>
                                    <div class="col-md-6">
                                        <label for="edit-owner-phone" class="form-label">Owner Phone</label>
                                        <input type="tel" class="form-control" id="edit-owner-phone" name="owner_phone" 
                                               pattern="[0-9\-\(\)\+\s]*" placeholder="(555) 123-4567">
                                    </div>
                                </div>

                                <!-- Address Information -->
                                <div class="section-header">
                                    <h6><i class="fas fa-map-marker-alt"></i> Address Information</h6>
                                </div>
                                <div class="row mb-3">
                                    <div class="col-12 mb-2">
                                        <label for="edit-address" class="form-label">Street Address</label>
                                        <input type="text" class="form-control" id="edit-address" name="address" 
                                               placeholder="123 Main Street">
                                    </div>
                                    <div class="col-md-4">
                                        <label for="edit-city" class="form-label">City</label>
                                        <input type="text" class="form-control" id="edit-city" name="city" required>
                                    </div>
                                    <div class="col-md-4">
                                        <label for="edit-state" class="form-label">State</label>
                                        <select class="form-select" id="edit-state" name="state" required>
                                            <option value="">Select State</option>
                                            <!-- States will be populated dynamically -->
                                        </select>
                                    </div>
                                    <div class="col-md-4">
                                        <label for="edit-zip" class="form-label">ZIP Code</label>
                                        <input type="text" class="form-control" id="edit-zip" name="zip_code" 
                                               pattern="[0-9]{5}(-[0-9]{4})?" placeholder="12345">
                                    </div>
                                </div>

                                <!-- Business Details -->
                                <div class="section-header">
                                    <h6><i class="fas fa-id-card"></i> Business Details</h6>
                                </div>
                                <div class="row mb-3">
                                    <div class="col-md-6">
                                        <label for="edit-ein" class="form-label">EIN</label>
                                        <input type="text" class="form-control" id="edit-ein" name="ein" 
                                               pattern="[0-9]{2}-[0-9]{7}" placeholder="12-3456789">
                                    </div>
                                    <div class="col-md-6">
                                        <label for="edit-npi" class="form-label">NPI</label>
                                        <input type="text" class="form-control" id="edit-npi" name="npi" 
                                               pattern="[0-9]{10}" placeholder="1234567890">
                                    </div>
                                </div>
                                <div class="row mb-3">
                                    <div class="col-md-6">
                                        <label for="edit-entity-type" class="form-label">Entity Type</label>
                                        <select class="form-select" id="edit-entity-type" name="entity_type">
                                            <option value="">Select Type</option>
                                            <option value="Individual">Individual</option>
                                            <option value="Organization">Organization</option>
                                            <option value="Partnership">Partnership</option>
                                            <option value="Corporation">Corporation</option>
                                            <option value="LLC">LLC</option>
                                        </select>
                                    </div>
                                    <div class="col-md-6">
                                        <label for="edit-providers" class="form-label">Number of Providers</label>
                                        <input type="number" class="form-control" id="edit-providers" name="providers" 
                                               min="1" max="999" placeholder="1">
                                    </div>
                                </div>
                                <div class="row mb-3">
                                    <div class="col-12">
                                        <label for="edit-specialties" class="form-label">Specialties</label>
                                        <textarea class="form-control" id="edit-specialties" name="specialties" 
                                                  rows="2" placeholder="Enter specialties separated by commas"></textarea>
                                    </div>
                                </div>
                                <div class="row mb-3">
                                    <div class="col-12">
                                        <div class="form-check">
                                            <input class="form-check-input" type="checkbox" id="edit-sole-proprietor" name="is_sole_proprietor">
                                            <label class="form-check-label" for="edit-sole-proprietor">
                                                Is Sole Proprietor
                                            </label>
                                        </div>
                                    </div>
                                </div>

                                <!-- Change Log -->
                                <div class="section-header">
                                    <h6><i class="fas fa-history"></i> Change Summary</h6>
                                </div>
                                <div id="change-summary" class="alert alert-info" style="display: none;">
                                    <strong>Changes detected:</strong>
                                    <ul id="change-list"></ul>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                                <i class="fas fa-times"></i> Cancel
                            </button>
                            <button type="button" class="btn btn-warning" id="reset-changes" style="display: none;">
                                <i class="fas fa-undo"></i> Reset Changes
                            </button>
                            <button type="button" class="btn btn-primary" id="save-lead-changes" disabled>
                                <i class="fas fa-save"></i> Save Changes
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Add modal to page if it doesn't exist
        if (!document.getElementById('leadEditModal')) {
            document.body.insertAdjacentHTML('beforeend', modalHTML);
        }

        this.modal = new bootstrap.Modal(document.getElementById('leadEditModal'));
        this.populateStateDropdown();
    }

    setupEventListeners() {
        const form = document.getElementById('leadEditForm');
        const saveBtn = document.getElementById('save-lead-changes');
        const resetBtn = document.getElementById('reset-changes');

        // Track form changes
        form.addEventListener('input', (e) => this.handleFormChange(e));
        form.addEventListener('change', (e) => this.handleFormChange(e));

        // Save changes
        saveBtn.addEventListener('click', () => this.saveChanges());

        // Reset changes
        resetBtn.addEventListener('click', () => this.resetForm());

        // Handle modal close with unsaved changes
        document.getElementById('leadEditModal').addEventListener('hide.bs.modal', (e) => {
            if (this.isDirty) {
                if (!confirm('You have unsaved changes. Are you sure you want to close without saving?')) {
                    e.preventDefault();
                }
            }
        });

        // Phone number formatting
        ['edit-practice-phone', 'edit-owner-phone'].forEach(id => {
            document.getElementById(id).addEventListener('input', this.formatPhoneNumber);
        });

        // EIN formatting
        document.getElementById('edit-ein').addEventListener('input', this.formatEIN);

        // ZIP validation
        document.getElementById('edit-zip').addEventListener('input', this.validateZIP);
    }

    openEditModal(leadId) {
        const lead = allLeads.find(l => l.id === leadId);
        if (!lead) {
            showNotification('Lead not found', 'error');
            return;
        }

        this.currentLead = { ...lead }; // Create a copy
        this.populateForm(lead);
        this.isDirty = false;
        this.updateUI();
        this.modal.show();
    }

    populateForm(lead) {
        document.getElementById('edit-practice-name').value = lead.practice_name || '';
        document.getElementById('edit-owner-name').value = lead.owner_name || '';
        document.getElementById('edit-practice-phone').value = lead.practice_phone || '';
        document.getElementById('edit-owner-phone').value = lead.owner_phone || '';
        document.getElementById('edit-address').value = lead.address || '';
        document.getElementById('edit-city').value = lead.city || '';
        document.getElementById('edit-state').value = lead.state || '';
        document.getElementById('edit-zip').value = lead.zip || '';
        document.getElementById('edit-ein').value = lead.ein || '';
        document.getElementById('edit-npi').value = lead.npi || '';
        document.getElementById('edit-entity-type').value = lead.entity_type || '';
        document.getElementById('edit-providers').value = lead.providers || 1;
        document.getElementById('edit-specialties').value = lead.specialties || '';
        document.getElementById('edit-sole-proprietor').checked = lead.is_sole_proprietor === 'True' || lead.is_sole_proprietor === true;
    }

    handleFormChange(e) {
        this.isDirty = true;
        this.updateUI();
        this.showChangeSummary();
    }

    updateUI() {
        const saveBtn = document.getElementById('save-lead-changes');
        const resetBtn = document.getElementById('reset-changes');
        
        saveBtn.disabled = !this.isDirty;
        resetBtn.style.display = this.isDirty ? 'inline-block' : 'none';
    }

    showChangeSummary() {
        const changes = this.getChanges();
        const summaryDiv = document.getElementById('change-summary');
        const changeList = document.getElementById('change-list');

        if (changes.length > 0) {
            changeList.innerHTML = changes.map(change => 
                `<li><strong>${change.field}:</strong> "${change.oldValue}" → "${change.newValue}"</li>`
            ).join('');
            summaryDiv.style.display = 'block';
        } else {
            summaryDiv.style.display = 'none';
        }
    }

    getChanges() {
        const changes = [];
        const form = document.getElementById('leadEditForm');
        const formData = new FormData(form);
        
        const fieldMap = {
            practice_name: 'Practice Name',
            owner_name: 'Owner Name',
            practice_phone: 'Practice Phone',
            owner_phone: 'Owner Phone',
            address: 'Address',
            city: 'City',
            state: 'State',
            zip_code: 'ZIP Code',
            ein: 'EIN',
            npi: 'NPI',
            entity_type: 'Entity Type',
            providers: 'Providers',
            specialties: 'Specialties'
        };

        for (const [key, label] of Object.entries(fieldMap)) {
            const newValue = formData.get(key) || '';
            const oldValue = this.currentLead[key] || this.currentLead[key.replace('_', '')] || '';
            
            if (newValue !== oldValue.toString()) {
                changes.push({
                    field: label,
                    oldValue: oldValue,
                    newValue: newValue
                });
            }
        }

        // Handle checkbox separately
        const isSoleProprietor = document.getElementById('edit-sole-proprietor').checked;
        const oldSoleProprietor = this.currentLead.is_sole_proprietor === 'True' || this.currentLead.is_sole_proprietor === true;
        
        if (isSoleProprietor !== oldSoleProprietor) {
            changes.push({
                field: 'Sole Proprietor',
                oldValue: oldSoleProprietor ? 'Yes' : 'No',
                newValue: isSoleProprietor ? 'Yes' : 'No'
            });
        }

        return changes;
    }

    async saveChanges() {
        if (!this.validateForm()) {
            return;
        }

        const saveBtn = document.getElementById('save-lead-changes');
        const originalText = saveBtn.innerHTML;
        
        try {
            saveBtn.disabled = true;
            saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';

            const formData = this.getFormData();
            const response = await this.updateLeadAPI(this.currentLead.id, formData);

            if (response.ok) {
                const updatedLead = await response.json();
                this.updateLocalLead(updatedLead);
                showNotification('Lead updated successfully!', 'success');
                this.modal.hide();
                renderLeadsTable(); // Refresh the table
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to update lead');
            }
        } catch (error) {
            console.error('Error updating lead:', error);
            showNotification(`Failed to update lead: ${error.message}`, 'error');
        } finally {
            saveBtn.disabled = false;
            saveBtn.innerHTML = originalText;
        }
    }

    getFormData() {
        const form = document.getElementById('leadEditForm');
        const formData = new FormData(form);
        
        return {
            practice_name: formData.get('practice_name'),
            owner_name: formData.get('owner_name'),
            practice_phone: formData.get('practice_phone'),
            owner_phone: formData.get('owner_phone'),
            address: formData.get('address'),
            city: formData.get('city'),
            state: formData.get('state'),
            zip_code: formData.get('zip_code'),
            ein: formData.get('ein'),
            npi: formData.get('npi'),
            entity_type: formData.get('entity_type'),
            providers: parseInt(formData.get('providers')) || 1,
            specialties: formData.get('specialties'),
            is_sole_proprietor: document.getElementById('edit-sole-proprietor').checked
        };
    }

    async updateLeadAPI(leadId, data) {
        const token = localStorage.getItem('auth_token');
        return fetch(`/api/v1/leads/${leadId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(data)
        });
    }

    updateLocalLead(updatedLead) {
        // Update the lead in allLeads array
        const index = allLeads.findIndex(l => l.id === updatedLead.id);
        if (index !== -1) {
            allLeads[index] = { ...allLeads[index], ...updatedLead };
        }

        // Update filtered leads if necessary
        const filteredIndex = filteredLeads.findIndex(l => l.id === updatedLead.id);
        if (filteredIndex !== -1) {
            filteredLeads[filteredIndex] = { ...filteredLeads[filteredIndex], ...updatedLead };
        }
    }

    validateForm() {
        const requiredFields = ['edit-practice-name', 'edit-city', 'edit-state'];
        let isValid = true;

        requiredFields.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (!field.value.trim()) {
                field.classList.add('is-invalid');
                isValid = false;
            } else {
                field.classList.remove('is-invalid');
            }
        });

        if (!isValid) {
            showNotification('Please fill in all required fields', 'error');
        }

        return isValid;
    }

    resetForm() {
        this.populateForm(this.currentLead);
        this.isDirty = false;
        this.updateUI();
        document.getElementById('change-summary').style.display = 'none';
    }

    populateStateDropdown() {
        const stateSelect = document.getElementById('edit-state');
        const states = [
            'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
            'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
            'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
            'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
            'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
        ];

        states.forEach(state => {
            const option = document.createElement('option');
            option.value = state;
            option.textContent = state;
            stateSelect.appendChild(option);
        });
    }

    // Utility formatting functions
    formatPhoneNumber(e) {
        let value = e.target.value.replace(/\D/g, '');
        if (value.length >= 6) {
            value = `(${value.slice(0, 3)}) ${value.slice(3, 6)}-${value.slice(6, 10)}`;
        } else if (value.length >= 3) {
            value = `(${value.slice(0, 3)}) ${value.slice(3)}`;
        }
        e.target.value = value;
    }

    formatEIN(e) {
        let value = e.target.value.replace(/\D/g, '');
        if (value.length >= 2) {
            value = `${value.slice(0, 2)}-${value.slice(2, 9)}`;
        }
        e.target.value = value;
    }

    validateZIP(e) {
        const value = e.target.value;
        const isValid = /^\d{5}(-\d{4})?$/.test(value) || value === '';
        e.target.classList.toggle('is-invalid', !isValid && value.length > 0);
    }
}

// Initialize the lead edit modal when the page loads
let leadEditModal;
document.addEventListener('DOMContentLoaded', function() {
    leadEditModal = new LeadEditModal();
});

// Function to open edit modal from buttons
function openLeadEditModal(leadId) {
    leadEditModal.openEditModal(leadId);
} 