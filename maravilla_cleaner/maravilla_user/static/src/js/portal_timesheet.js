// Make functions globally available immediately
window.showTimesheetPopup = showTimesheetPopup;
window.closeTimesheetPopup = closeTimesheetPopup;
window.saveTimesheet = saveTimesheet;

// Global variables
let currentTimesheetOverlay = null;
let currentTaskId = null;

// Toast notification function
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    const bgColor = type === 'success' ? '#28a745' : '#dc3545';
    const icon = type === 'success' ? '✓' : '✗';

    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${bgColor};
        color: white;
        padding: 15px 20px;
        border-radius: 4px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10000;
        display: flex;
        align-items: center;
        gap: 10px;
        animation: slideIn 0.3s ease, fadeOut 0.3s ease 2.7s;
        animation-fill-mode: forwards;
        max-width: 350px;
        word-break: break-word;
    `;

    toast.innerHTML = `
        <span style="font-weight: bold; font-size: 16px; flex-shrink: 0;">${icon}</span>
        <span style="flex: 1;">${message}</span>
    `;

    // Add CSS animations if not already added
    if (!document.getElementById('toast-styles')) {
        const style = document.createElement('style');
        style.id = 'toast-styles';
        style.textContent = `
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            @keyframes fadeOut {
                from { opacity: 1; }
                to { opacity: 0; }
            }
        `;
        document.head.appendChild(style);
    }

    // Remove existing toasts to prevent stacking
    const existingToasts = document.querySelectorAll('[data-toast]');
    existingToasts.forEach(t => t.remove());

    toast.setAttribute('data-toast', 'true');
    document.body.appendChild(toast);

    // Auto-remove after 3 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.remove();
        }
    }, 3000);
}

// Get task ID and task name from current page
function getTaskInfo() {
    const taskId = window.location.pathname.split('/').pop();
    const taskName = document.querySelector('h1, h2, .o_portal_task_name')?.textContent?.trim() || 'Current Task';
    return { taskId, taskName };
}

// Create and show the timesheet popup
function showTimesheetPopup() {
    const { taskId, taskName } = getTaskInfo();

    // Create overlay
    const overlay = document.createElement('div');
    overlay.style.cssText = 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 9999; display: flex; align-items: center; justify-content: center;';

    // Create modal
    const modal = document.createElement('div');
    modal.style.cssText = 'background: white; padding: 20px; border-radius: 8px; width: 500px; max-width: 90%; box-shadow: 0 4px 6px rgba(0,0,0,0.1);';

    // Get today's date for default value
    const today = new Date().toISOString().split('T')[0];

    modal.innerHTML = '<div style="border-bottom: 1px solid #dee2e6; padding-bottom: 15px; margin-bottom: 15px;">' +
        '<h4 style="margin: 0; color: #333;">Add Timesheet Entry</h4>' +
        '<p style="margin: 5px 0 0 0; color: #666; font-size: 14px;">Task: ' + taskName + ' (ID: ' + taskId + ')</p>' +
        '</div>' +

        // Date Field
        '<div style="margin-bottom: 15px;">' +
        '<label style="display: block; margin-bottom: 5px; font-weight: bold;">Date</label>' +
        '<input type="date" id="timesheet_date" class="form-control" value="' + today + '" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;" required>' +
        '</div>' +

        // Time Spent Field
        '<div style="margin-bottom: 15px;">' +
        '<label style="display: block; margin-bottom: 5px; font-weight: bold;">Time Spent (Hours)</label>' +
        '<input type="number" id="timesheet_hours" class="form-control" step="0.1" min="0.1" max="24" placeholder="Enter hours worked" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;" required>' +
        '</div>' +

        // Description Field
        '<div style="margin-bottom: 20px;">' +
        '<label style="display: block; margin-bottom: 5px; font-weight: bold;">Description</label>' +
        '<textarea id="timesheet_description" class="form-control" rows="3" placeholder="Describe the work you performed..." style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;" required></textarea>' +
        '</div>' +

        // Buttons
        '<div style="display: flex; justify-content: space-between;">' +
        '<button type="button" id="cancelTimesheetBtn" style="padding: 8px 16px; background: #6c757d; color: white; border: none; border-radius: 4px; cursor: pointer;">Cancel</button>' +
        '<button type="button" id="saveTimesheetBtn" style="padding: 8px 16px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">Save Timesheet</button>' +
        '</div>';

    overlay.appendChild(modal);
    document.body.appendChild(overlay);

    // Add event listeners to the buttons
    document.getElementById('cancelTimesheetBtn').addEventListener('click', closeTimesheetPopup);
    document.getElementById('saveTimesheetBtn').addEventListener('click', saveTimesheet);

    // Store reference for closing
    currentTimesheetOverlay = overlay;
    currentTaskId = taskId;
}

// Close the timesheet popup
function closeTimesheetPopup() {
    if (currentTimesheetOverlay) {
        currentTimesheetOverlay.remove();
        currentTimesheetOverlay = null;
    }
}

// Save timesheet function
function saveTimesheet() {
    // Get values from form
    const date = document.getElementById('timesheet_date').value;
    const hours = document.getElementById('timesheet_hours').value;
    const description = document.getElementById('timesheet_description').value;
    const taskId = currentTaskId;

    // Validate form
    if (!date) {
        showToast('Please select a date', 'error');
        return;
    }

    if (!hours || parseFloat(hours) <= 0) {
        showToast('Please enter a valid number of hours', 'error');
        return;
    }

    if (!description) {
        showToast('Please enter a description', 'error');
        return;
    }

    // Show saving state
    const saveBtn = document.getElementById('saveTimesheetBtn');
    const originalText = saveBtn.textContent;
    saveBtn.textContent = 'Saving...';
    saveBtn.disabled = true;

    // Use the global rpc object directly
    if (window.odoo && window.odoo.__DEBUG__ && window.odoo.__DEBUG__.services) {
        const rpc = window.odoo.__DEBUG__.services['web.core'].rpc;

        // Direct RPC call
        rpc.query({
            model: 'account.analytic.line',
            method: 'create',
            args: [{
                'task_id': parseInt(taskId),
                'date': date,
                'unit_amount': parseFloat(hours),
                'name': description,
            }]
        }).then(function(result) {
            console.log("Timesheet created with ID:", result);
            closeTimesheetPopup();
            showToast('Timesheet added successfully!', 'success');
            setTimeout(() => location.reload(), 1000);
        }).catch(function(error) {
            console.error("Error creating timesheet:", error);
            showToast('Error saving timesheet: ' + error.message, 'error');
            saveBtn.textContent = originalText;
            saveBtn.disabled = false;
        });
    } else {
        // Alternative method using fetch API
        saveTimesheetWithFetch(date, hours, description, taskId, saveBtn, originalText);
    }
}

// Fallback method using fetch API
function saveTimesheetWithFetch(date, hours, description, taskId, saveBtn, originalText) {
    const data = {
        jsonrpc: "2.0",
        method: "call",
        params: {
            model: 'account.analytic.line',
            method: 'create',
            args: [{
                'task_id': parseInt(taskId),
                'date': date,
                'unit_amount': parseFloat(hours),
                'name': description,
            }],
            kwargs: {}
        },
        id: Math.floor(Math.random() * 1000)
    };

    fetch('/web/dataset/call_kw', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.error) {
            throw new Error(result.error.data.message);
        }
        console.log("Timesheet created with ID:", result.result);
        closeTimesheetPopup();
        showToast('Timesheet added successfully!', 'success');
        setTimeout(() => location.reload(), 1000);
    })
    .catch(error => {
        console.error("Error creating timesheet:", error);
        showToast('Error saving timesheet: ' + error.message, 'error');
        if (saveBtn && originalText) {
            saveBtn.textContent = originalText;
            saveBtn.disabled = false;
        }
    });
}

// Test function for debugging
function testRPC() {
    if (window.odoo && window.odoo.__DEBUG__ && window.odoo.__DEBUG__.services) {
        const rpc = window.odoo.__DEBUG__.services['web.core'].rpc;
        console.log("RPC service available");
        return true;
    } else {
        console.log("RPC service not available, will use fetch API");
        return false;
    }
}

// Initialize event listeners when DOM is loaded
function initializeTimesheetButtons() {
    // Remove any existing onclick handlers and use event listeners instead
    const addButton = document.getElementById('btn_add_timesheet');
    if (addButton) {
        // Remove the onclick attribute if it exists
        addButton.removeAttribute('onclick');
        // Add event listener
        addButton.addEventListener('click', showTimesheetPopup);
    }

    // Test RPC on load (optional)
    setTimeout(testRPC, 1000);
}

// ALSO add a fallback for any existing onclick attributes in the page
function fixExistingOnclickHandlers() {
    // Find any elements with onclick calling showTimesheetPopup
    const elements = document.querySelectorAll('[onclick*="showTimesheetPopup"]');
    elements.forEach(element => {
        // Replace the onclick with our event listener
        const oldOnclick = element.getAttribute('onclick');
        element.removeAttribute('onclick');
        element.addEventListener('click', showTimesheetPopup);
        console.log('Fixed onclick handler for:', element);
    });
}

// Initialize when document is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        initializeTimesheetButtons();
        fixExistingOnclickHandlers();
    });
} else {
    initializeTimesheetButtons();
    fixExistingOnclickHandlers();
}