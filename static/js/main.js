const API_BASE_URL = '/api/students';
let students = [];
let currentEditId = null;
let searchTimeout = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    loadStudents();
    setupEventListeners();
    setupMobileInputFormatting();
});

// Setup mobile number input formatting
function setupMobileInputFormatting() {
    const mobileInput = document.getElementById('mobile');
    if (mobileInput) {
        mobileInput.addEventListener('input', function(e) {
            // Remove non-digit characters
            this.value = this.value.replace(/\D/g, '');
            // Limit to 10 digits
            if (this.value.length > 10) {
                this.value = this.value.slice(0, 10);
            }
        });
    }
}

// Setup event listeners
function setupEventListeners() {
    // Search functionality
    const searchInput = document.getElementById('searchInput');
    searchInput.addEventListener('input', handleSearch);
    
    document.getElementById('clearSearch').addEventListener('click', () => {
        searchInput.value = '';
        loadStudents();
    });

    // Add student button
    document.getElementById('addStudentBtn').addEventListener('click', () => {
        openModal('add');
    });

    // Refresh button
    document.getElementById('refreshBtn').addEventListener('click', () => {
        loadStudents(document.getElementById('searchInput').value.trim());
        showToast('Data refreshed from database', 'success');
    });

    // Modal close - use multiple methods to ensure it works
    const closeBtn = document.querySelector('.close');
    if (closeBtn) {
        closeBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            closeModal();
        });
    }
    
    const cancelBtn = document.getElementById('cancelBtn');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', closeModal);
    }
    
    // Close modal when clicking outside
    window.addEventListener('click', (e) => {
        const modal = document.getElementById('studentModal');
        if (e.target === modal) {
            closeModal();
        }
    });

    // Form submit
    document.getElementById('studentForm').addEventListener('submit', handleFormSubmit);

    // Import Excel
    document.getElementById('importFile').addEventListener('change', handleImport);

    // Export Excel
    document.getElementById('exportBtn').addEventListener('click', handleExport);

    // Clear All Data
    document.getElementById('clearAllBtn').addEventListener('click', handleClearAll);
}

// Load all students
async function loadStudents(searchQuery = '') {
    try {
        const url = searchQuery ? `${API_BASE_URL}?search=${encodeURIComponent(searchQuery)}` : API_BASE_URL;
        const response = await fetch(url);
        
        // Check if response is JSON
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            throw new Error(`Server returned non-JSON response: ${text.substring(0, 100)}`);
        }
        
        const data = await response.json();
        
        // Check if response contains an error
        if (!response.ok && data.error) {
            showToast(data.error, 'error');
            renderStudents([]);
            return;
        }
        
        students = data;
        renderStudents(data);
    } catch (error) {
        showToast('Error loading students: ' + error.message, 'error');
        console.error('Error:', error);
        renderStudents([]);
    }
}

// Handle search with debounce
function handleSearch(e) {
    const query = e.target.value.trim();
    
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        loadStudents(query);
    }, 300);
}

// Render students table
function renderStudents(studentsData) {
    const tbody = document.getElementById('studentsTableBody');
    const noResults = document.getElementById('noResults');
    
    if (studentsData.length === 0) {
        tbody.innerHTML = '';
        noResults.style.display = 'block';
        return;
    }
    
    noResults.style.display = 'none';
    
    tbody.innerHTML = studentsData.map(student => {
        // Ensure all fields are present, use empty string if missing
        const regNo = student.reg_no || student.regNo || '';
        const name = student.name || '';
        const email = student.email || '';
        const mobile = student.mobile || '';
        const address = student.address || '';
        const id = student._id || student.id || '';
        
        return `
        <tr>
            <td>${escapeHtml(regNo)}</td>
            <td>${escapeHtml(name)}</td>
            <td>${escapeHtml(email)}</td>
            <td>${escapeHtml(mobile)}</td>
            <td>${escapeHtml(address)}</td>
            <td>
                <button class="btn-edit" onclick="editStudent('${id}')">Edit</button>
                <button class="btn-delete" onclick="deleteStudent('${id}')">Delete</button>
            </td>
        </tr>
        `;
    }).join('');
}

// Open modal for add or edit
function openModal(mode, studentId = null) {
    const modal = document.getElementById('studentModal');
    const form = document.getElementById('studentForm');
    const title = document.getElementById('modalTitle');
    
    if (mode === 'add') {
        title.textContent = 'Add New Student';
        form.reset();
        document.getElementById('studentId').value = '';
        currentEditId = null;
    } else if (mode === 'edit' && studentId) {
        title.textContent = 'Edit Student';
        currentEditId = studentId;
        loadStudentData(studentId);
    }
    
    modal.style.display = 'block';
}

// Load student data for editing
async function loadStudentData(studentId) {
    try {
        const response = await fetch(`${API_BASE_URL}/${studentId}`);
        
        // Check if response is JSON
        const contentType = response.headers.get('content-type');
        let student;
        if (contentType && contentType.includes('application/json')) {
            student = await response.json();
        } else {
            const text = await response.text();
            throw new Error(`Server returned non-JSON response: ${text.substring(0, 100)}`);
        }
        
        if (!response.ok && student.error) {
            showToast(student.error, 'error');
            return;
        }
        
        document.getElementById('studentId').value = student._id;
        document.getElementById('regNo').value = student.reg_no;
        document.getElementById('name').value = student.name;
        document.getElementById('email').value = student.email;
        document.getElementById('mobile').value = student.mobile;
        document.getElementById('address').value = student.address;
    } catch (error) {
        showToast('Error loading student data: ' + error.message, 'error');
        console.error('Error:', error);
    }
}

// Close modal
function closeModal() {
    const modal = document.getElementById('studentModal');
    if (modal) {
        modal.style.display = 'none';
    }
    const form = document.getElementById('studentForm');
    if (form) {
        form.reset();
    }
    currentEditId = null;
}

// Make closeModal globally accessible for onclick handlers
window.closeModal = closeModal;

// Validate form fields
function validateForm(formData) {
    const errors = [];
    
    // Validate name (letters, spaces, hyphens, apostrophes, dots)
    const namePattern = /^[a-zA-Z\s.\'-]+$/;
    if (!namePattern.test(formData.name) || formData.name.length < 2) {
        errors.push('Name should contain only letters and be at least 2 characters long');
    }
    
    // Validate email
    const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    if (!emailPattern.test(formData.email)) {
        errors.push('Please enter a valid email address');
    }
    
    // Validate mobile (exactly 10 digits)
    const mobileClean = formData.mobile.replace(/\D/g, '');
    if (mobileClean.length !== 10 || !/^\d{10}$/.test(mobileClean)) {
        errors.push('Mobile number must be exactly 10 digits');
    }
    
    // Validate address
    if (formData.address.length < 5) {
        errors.push('Address must be at least 5 characters long');
    }
    
    return errors;
}

// Handle form submit
async function handleFormSubmit(e) {
    e.preventDefault();
    
    const formData = {
        reg_no: document.getElementById('regNo').value.trim(),
        name: document.getElementById('name').value.trim(),
        email: document.getElementById('email').value.trim(),
        mobile: document.getElementById('mobile').value.trim(),
        address: document.getElementById('address').value.trim()
    };
    
    // Client-side validation
    const validationErrors = validateForm(formData);
    if (validationErrors.length > 0) {
        showToast(validationErrors[0], 'error');
        return;
    }
    
    // Clean mobile number (remove non-digits)
    formData.mobile = formData.mobile.replace(/\D/g, '');
    
    try {
        const studentId = document.getElementById('studentId').value;
        const url = studentId ? `${API_BASE_URL}/${studentId}` : API_BASE_URL;
        const method = studentId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        // Check if response is JSON
        const contentType = response.headers.get('content-type');
        let data;
        if (contentType && contentType.includes('application/json')) {
            data = await response.json();
        } else {
            const text = await response.text();
            throw new Error(`Server returned non-JSON response: ${text.substring(0, 100)}`);
        }
        
        if (response.ok) {
            showToast(studentId ? 'Student updated successfully in database!' : 'Student added successfully to database!', 'success');
            closeModal();
            // Automatically refresh to show updated data from database
            setTimeout(() => {
                loadStudents(document.getElementById('searchInput').value.trim());
            }, 500);
        } else {
            showToast(data.error || 'Error saving student', 'error');
        }
    } catch (error) {
        showToast('Error saving student: ' + error.message, 'error');
        console.error('Error:', error);
    }
}

// Edit student - make globally accessible
function editStudent(studentId) {
    openModal('edit', studentId);
}
window.editStudent = editStudent;

// Delete student
async function deleteStudent(studentId) {
    if (!confirm('Are you sure you want to delete this student?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/${studentId}`, {
            method: 'DELETE'
        });
        
        // Check if response is JSON
        const contentType = response.headers.get('content-type');
        let data;
        if (contentType && contentType.includes('application/json')) {
            data = await response.json();
        } else {
            const text = await response.text();
            throw new Error(`Server returned non-JSON response: ${text.substring(0, 100)}`);
        }
        
        if (response.ok) {
            showToast('Student deleted successfully from database!', 'success');
            // Automatically refresh to show updated data from database
            setTimeout(() => {
                loadStudents(document.getElementById('searchInput').value.trim());
            }, 500);
        } else {
            showToast(data.error || 'Error deleting student', 'error');
        }
    } catch (error) {
        showToast('Error deleting student: ' + error.message, 'error');
        console.error('Error:', error);
    }
}
window.deleteStudent = deleteStudent;

// Handle Excel import
async function handleImport(e) {
    const file = e.target.files[0];
    if (!file) {
        showToast('No file selected', 'error');
        return;
    }
    
    // Show loading message
    showToast('Uploading and importing file to database...', 'success');
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch(`${API_BASE_URL}/import`, {
            method: 'POST',
            body: formData
        });
        
        // Check if response is JSON
        const contentType = response.headers.get('content-type');
        let data;
        if (contentType && contentType.includes('application/json')) {
            data = await response.json();
        } else {
            const text = await response.text();
            throw new Error(`Server returned non-JSON response: ${text.substring(0, 100)}`);
        }
        
        if (response.ok) {
            // Show appropriate message based on import results
            if (data.imported > 0) {
                if (data.errors && data.errors.length > 0) {
                    showToast(`${data.imported} student(s) imported successfully! ${data.errors.length} row(s) had errors.`, 'success');
                    // Show detailed errors in console
                    console.warn('Import errors:', data.errors);
                } else {
                    showToast(`${data.imported} student(s) imported and saved to MongoDB database!`, 'success');
                }
            } else {
                // No students imported
                if (data.errors && data.errors.length > 0) {
                    // Show the first error message to help user understand what went wrong
                    const firstError = data.errors[0];
                    const errorCount = data.errors.length;
                    const errorMsg = errorCount === 1 
                        ? `Import failed: ${firstError}` 
                        : `Import failed: ${firstError} (and ${errorCount - 1} more error${errorCount - 1 > 1 ? 's' : ''})`;
                    showToast(errorMsg, 'error');
                    console.warn('All import errors:', data.errors);
                    
                    // Show all errors in console for debugging
                    if (data.errors.length > 1) {
                        console.warn('Additional errors:', data.errors.slice(1));
                    }
                } else {
                    showToast('No valid student data found in Excel file. Please check the file format.', 'error');
                }
            }
            
            // Automatically refresh to show imported data from database
            setTimeout(() => {
                loadStudents(document.getElementById('searchInput').value.trim());
            }, 500);
        } else {
            showToast(data.error || 'Error importing file', 'error');
        }
    } catch (error) {
        showToast('Error importing file: ' + error.message, 'error');
        console.error('Error:', error);
    }
    
    // Reset file input
    e.target.value = '';
}

// Handle Excel export
async function handleExport() {
    try {
        showToast('Exporting data from database...', 'success');
        const response = await fetch(`${API_BASE_URL}/export`);
        
        // Check if response is JSON (error) or blob (file)
        const contentType = response.headers.get('content-type');
        
        if (response.ok && contentType && contentType.includes('application/vnd.openxmlformats')) {
            // It's an Excel file
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'students.xlsx';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            showToast('Students exported successfully from database!', 'success');
        } else {
            // It's an error response
            const text = await response.text();
            let errorData;
            try {
                errorData = JSON.parse(text);
            } catch {
                errorData = { error: text.substring(0, 100) };
            }
            showToast(errorData.error || 'Error exporting file', 'error');
        }
    } catch (error) {
        showToast('Error exporting file: ' + error.message, 'error');
        console.error('Error:', error);
    }
}

// Handle Clear All Data
async function handleClearAll() {
    // Double confirmation
    const confirm1 = confirm('WARNING: This will delete ALL student records. This action cannot be undone!\n\nAre you sure you want to continue?');
    if (!confirm1) return;
    
    const confirm2 = confirm('This is your last chance. Click OK to permanently delete all student data.');
    if (!confirm2) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/clear`, {
            method: 'DELETE'
        });
        
        // Check if response is JSON
        const contentType = response.headers.get('content-type');
        let data;
        if (contentType && contentType.includes('application/json')) {
            data = await response.json();
        } else {
            const text = await response.text();
            throw new Error(`Server returned non-JSON response: ${text.substring(0, 100)}`);
        }
        
        if (response.ok) {
            showToast(`Successfully deleted ${data.deleted_count} student(s) from database`, 'success');
            // Automatically refresh to show updated data from database
            setTimeout(() => {
                loadStudents(document.getElementById('searchInput').value.trim());
            }, 500);
        } else {
            showToast(data.error || 'Error clearing data', 'error');
        }
    } catch (error) {
        showToast('Error clearing data: ' + error.message, 'error');
        console.error('Error:', error);
    }
}

// Show toast notification
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    
    // Show error messages longer so users can read them
    const displayTime = type === 'error' ? 5000 : 3000;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, displayTime);
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

