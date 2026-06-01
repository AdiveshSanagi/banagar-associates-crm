// =========================================================================
// BANAGAR ASSOCIATES - MASTER ADMINISTRATIVE WORKSPACE RUNTIME
// Location: /frontend/admin.js
// =========================================================================

let currentCalendarDate = new Date(); // Global pointer tracking current viewed month/year index

// =========================================================================
// 1. ALL ON-LOAD INITIALIZATIONS (DOMContentLoaded MASTER ENGINE)
// =========================================================================
document.addEventListener("DOMContentLoaded", () => {
    const loginForm = document.getElementById("admin-login-form");

    // --- ADMINISTRATIVE AUTHENTICATION CONTROL LAYER (adminlogin.html) ---
    if (loginForm) {
        loginForm.addEventListener("submit", async (e) => {
            e.preventDefault();

            const email = document.getElementById("admin-email").value.trim();
            const password = document.getElementById("admin-password").value.trim();
            const submitBtn = loginForm.querySelector("button[type='submit']");

            try {
                if (submitBtn) {
                    submitBtn.disabled = true;
                    submitBtn.innerText = "Securing Authentication Session...";
                }

                await ApiService.adminLogin(email, password);

               showModernPopup("Authentication verified! Redirecting to secure control board...");
                window.location.href = "admin.html";

            } catch (err) {
                showModernPopup(`Authentication Blocked: ${err.message}`, '', 'error');
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerText = "Login";
                }
            }
        });
    }

    // --- SECURE WORKSPACE DASHBOARD DATA SYNC PIPELINES (admin.html) ---
    if (window.location.pathname.includes("admin.html")) {
        // Strict Security Gateway Guard
        if (!localStorage.getItem("admin_token")) {
           showModernPopup("Access Denied: Invalid Security Session Token Context.");
            window.location.href = "adminlogin.html"; // Ensure this points to your login page
            return;
        }

        // Initialize live operational components and dynamic rows straight out of MySQL
        loadDashboardAnalytics();
        initializeAdminProfileCard();
        loadMasterBookingsTable();
        loadCustomerQueriesTable();
        loadDashboardCalendar(); 
        loadAdminGalleryManager();

        // Handle Admin Password Updates from Profile Modal
        const profileForm = document.getElementById("admin-profile-form");
        if (profileForm) {
            profileForm.addEventListener("submit", async (e) => {
                e.preventDefault();
                
                const newPassword = document.getElementById("profile-password").value;
                const saveBtn = document.getElementById("btn-save-profile");

                if (newPassword.trim().length < 6) {
                   showModernPopup("Security Exception: New password must be at least 6 characters long.");
                    return;
                }

                try {
                    if (saveBtn) {
                        saveBtn.disabled = true;
                        saveBtn.innerText = "Hashing & Saving...";
                    }

                    await ApiService.updateAdminPassword({ new_password: newPassword });

                   showModernPopup("Security context altered successfully! Please use your new password next time you login.");
                    document.getElementById("profile-password").value = ""; 
                    
                    const modalEl = document.getElementById('profileModal');
                    const modalInstance = bootstrap.Modal.getInstance(modalEl);
                    if (modalInstance) modalInstance.hide();

                } catch (err) {
                    showModernPopup(`Security Patch Terminated: ${err.message}`, '', 'error');
                } finally {
                    if (saveBtn) {
                        saveBtn.disabled = false;
                        saveBtn.innerText = "Save Changes";
                    }
                }
            });
        }

        // Bind secure session termination hook
        const logoutBtn = document.getElementById("btn-secure-logout");
        if (logoutBtn) {
            logoutBtn.addEventListener("click", async (e) => {
                e.preventDefault();

                // Cinematic confirmation popup
                const result = await Swal.fire({
                    title: 'Terminate Session',
                    text: "Are you sure you want to end your administrative session?",
                    icon: 'warning',
                    showCancelButton: true,
                    confirmButtonText: 'Yes, Logout',
                    cancelButtonText: 'Stay',
                    background: '#141923', // Matches your UI theme
                    color: '#ffffff',
                    confirmButtonColor: '#dc3545', // Danger red for logout
                    cancelButtonColor: '#6c757d'
                });

                if (result.isConfirmed) {
                    ApiService.logout();
                }
            });
        }
        // Bind multi-part asset file gallery upload form submission hook
        const galleryForm = document.getElementById("gallery-upload-form");
        if (galleryForm) {
            galleryForm.addEventListener("submit", handleMediaAssetUpload);
        }

        const fileInput = document.getElementById("gallery-file-input");
        if (fileInput) {
            fileInput.addEventListener("change", (e) => {
                const zoneText = document.getElementById("upload-zone-text");
                if (zoneText && e.target.files.length > 0) {
                    zoneText.innerText = `Selected: ${e.target.files[0].name}`;
                }
            });
        }
    }
});

// =========================================================================
// 2. SIDEBAR WORKSPACE NAV VIEWS & PROFILE AVATAR MANAGEMENT
// =========================================================================
window.switchView = function(viewId) {
    document.querySelectorAll('.view-panel').forEach(panel => panel.classList.remove('active-view'));
    document.querySelectorAll('.admin-nav-link').forEach(link => link.classList.remove('active-tab'));
    
    const targetPanel = document.getElementById('view-' + viewId);
    if (targetPanel) {
        targetPanel.classList.add('active-view');
    }
    if (event && event.currentTarget) {
        event.currentTarget.classList.add('active-tab');
    }

    // Trigger data load when clicked
    if (viewId === 'completed') {
        loadCompletedBookingsTable();
    }
};

window.previewAvatar = function(event) {
    const input = event.target;
    const previewImage = document.getElementById('admin-avatar-preview');
    
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            if (previewImage) previewImage.src = e.target.result;
        }
        reader.readAsDataURL(input.files[0]);
    }
};

function initializeAdminProfileCard() {
    const fullNameField = document.getElementById("profile-fullname");
    const emailField = document.getElementById("profile-email");

    if (fullNameField && emailField) {
        fullNameField.value = "System Admin";
        emailField.value = "admin@banagar.com";
    }
}

// =========================================================================
// 3. CORE ANALYTICAL Snapshots & LIVE MYSQL DATA LEDGERS
// =========================================================================
async function loadDashboardAnalytics() {
    try {
        const stats = await ApiService.getDashboardStats();
        const elementsMap = {
            "stat-total-bookings": stats.total_bookings,
            "stat-confirmed-bookings": stats.confirmed_bookings,
            "stat-pending-bookings": stats.pending_bookings,
            "stat-total-enquiries": stats.total_enquiries,
            "stat-new-enquiries": stats.new_enquiries_this_month,
            "stat-total-revenue": `₹${stats.total_revenue_collected.toLocaleString('en-IN')}`
        };

        Object.entries(elementsMap).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) element.innerText = value;
        });
    } catch (err) {
        console.error("Dashboard metric analytical compilation loop failure:", err.message);
    }
}

async function loadMasterBookingsTable() {
    const masterTableBody = document.getElementById("admin-bookings-rows");
    const recentTableBody = document.getElementById("admin-recent-bookings-rows");
    
    if (!masterTableBody && !recentTableBody) return;

    try {
        const bookings = await ApiService.getAllBookings(); 
        window.globalBookings = bookings; 

        // Centralized row generation logic
        const generateRowHtml = (b) => {
            // 1. Set the badge colors based on new statuses
            let badgeStyle = "bg-pending"; // Default
            if (b.booking_status === "Confirmed") badgeStyle = "bg-confirmed";
            if (b.booking_status === "Completed") badgeStyle = "bg-success"; // Green for completed
            if (b.booking_status === "Cancelled") badgeStyle = "bg-danger";
            
            // 2. Fallback Total Rent if missing from DB
            let totalRent = b.total_amount;
            if(!totalRent) {
                if(b.venue_type === 'Banagar Lawns') totalRent = 150000;
                else if(b.venue_type === 'Banagar Marriage Hall') totalRent = 200000;
                else totalRent = 300000;
            }

            // 3. Smart Money Logic: Shows ₹0, 20%, or 100% depending on admin button clicks
            let amountPaidDisplay = "₹0";
            if (b.booking_status === "Confirmed") {
                amountPaidDisplay = `₹${Number(b.advance_paid || 25000).toLocaleString('en-IN')}`;
            } else if (b.booking_status === "Completed") {
                amountPaidDisplay = `₹${Number(totalRent).toLocaleString('en-IN')}`;
            }
            let quoteDisplay = Number(totalRent).toLocaleString('en-IN');

            // 4. Return the 10 clean HTML columns
            return `
                <tr>
                    
                    <td class="text-info">#${b.id}</td>
                    <td class="text-white"><strong>${b.customer_name}</strong></td>
                    <td>${b.venue_type}</td>
                    <td>${b.event_type || 'N/A'}</td>
                    <td class="text-muted fs-8">${new Date(b.event_date).toLocaleDateString('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric' })}</td>
                    <td>${b.phone}</td>
                    <td>${b.guest_count || '0'}</td>
                    
                    <td>
                        <span class="text-gold fw-bold d-block">${amountPaidDisplay} Paid</span>
                        <small class="text-muted">Total: ₹${quoteDisplay}</small>
                    </td>
                    
                    <td><span class="status-badge ${badgeStyle}">${b.booking_status.toUpperCase()}</span></td>
                    
                    <td>
                        <div class="action-icon-group justify-content-end">
                            <button class="btn-icon confirm" title="Confirm (Advance Paid)" onclick="updateBookingStatus('${b.id}', 'Confirmed')"><i class="bi bi-check-lg"></i></button>
                            <button class="btn-icon" style="background: none; border: none; color: #198754;" title="Complete (Fully Paid)" onclick="updateBookingStatus('${b.id}', 'Completed')"><i class="bi bi-check-all fs-5"></i></button>
                            <button class="btn-icon delete" title="Cancel Booking" onclick="updateBookingStatus('${b.id}', 'Cancelled')"><i class="bi bi-x-lg"></i></button>
                        </div>
                    </td>
                </tr>`;
        };

        // RENDER MASTER LEDGER
        if (masterTableBody) {
            masterTableBody.innerHTML = "";
            if (bookings.length === 0) {
                masterTableBody.innerHTML = `<tr><td colspan="10" class="text-center text-muted py-4">No bookings found in the database.</td></tr>`;
            } else {
                bookings.forEach(b => { masterTableBody.insertAdjacentHTML("beforeend", generateRowHtml(b)); });
            }
        }

        // RENDER RECENT BOOKINGS
        if (recentTableBody) {
            recentTableBody.innerHTML = "";
            const recentBookings = bookings.slice(-5).reverse(); 
            if (recentBookings.length === 0) {
                recentTableBody.innerHTML = `<tr><td colspan="10" class="text-center text-muted py-4">No recent booking activity.</td></tr>`;
            } else {
                recentBookings.forEach(b => { recentTableBody.insertAdjacentHTML("beforeend", generateRowHtml(b)); });
            }
        }

        if (typeof loadDashboardCalendar === 'function') {
            loadDashboardCalendar();
        }

    } catch (err) {
        console.error("Error loading master data array grid instance:", err);
        if (masterTableBody) masterTableBody.innerHTML = `<tr><td colspan="10" class="text-center text-danger py-4">Failed to connect to the backend database. (${err.message})</td></tr>`;
    }
}
async function loadCustomerQueriesTable() {
    const tableBody = document.getElementById("admin-queries-rows");
    if (!tableBody) return;

    try {
        const queries = await ApiService.getAllQueries();
        tableBody.innerHTML = "";

        if (queries.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="6" class="text-center text-muted py-4">No consumer leads received yet.</td></tr>`;
            return;
        }

        queries.forEach(q => {
            const rowHtml = `
                <tr>
                    <td><small>${new Date(q.received_time).toLocaleDateString()}</small></td>
                    <td><strong>${q.name}</strong><br></td>
                    <td><small class="text-light">${q.phone}</small></td>
                    <td><small class="text-muted">${q.email || 'No Email Provided'}</small></td>
                    <td>${q.event_date || 'N/A'}</td>
                    <td><p class="mb-0 small text-wrap" style="max-width: 250px;">${q.message}</p></td>
                    <td>
                        <div class="action-icon-group">
                            <a href="tel:${q.phone}" class="btn-icon edit" title="Call Client"><i class="bi bi-telephone"></i></a>
                            <a href="https://wa.me/${q.phone.replace(/[^0-9]/g, '')}" target="_blank" class="btn-icon confirm" title="WhatsApp Client"><i class="bi bi-whatsapp"></i></a>
                        </div>
                    </td>
                </tr>`;
            tableBody.insertAdjacentHTML("beforeend", rowHtml);
        });
    } catch (err) {
        console.error("Error handling interactive lead query ingestion:", err);
    }
}

// =========================================================================
// 4. BACKEND-CONNECTED REAL-TIME AVAILABILITY CALENDAR ENGINE
// =========================================================================
async function loadDashboardCalendar() {
    const calendarGrid = document.getElementById("dynamic-calendar");
    const monthYearLabel = document.getElementById("calendar-month-year");
    if (!calendarGrid || !monthYearLabel) return;

    try {
        const blockedDates = await ApiService.getBookedDates(); 
        calendarGrid.innerHTML = "";

        const year = currentCalendarDate.getFullYear();
        const month = currentCalendarDate.getMonth();

        const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
        monthYearLabel.innerText = `${monthNames[month]} ${year}`;

        const daysOfWeek = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
        daysOfWeek.forEach(d => {
            calendarGrid.insertAdjacentHTML("beforeend", `<div class="calendar-header-cell text-muted fw-semibold small text-center py-1">${d}</div>`);
        });

        const firstDayIndex = new Date(year, month, 1).getDay();
        const totalDaysInMonth = new Date(year, month + 1, 0).getDate();

        for (let i = 0; i < firstDayIndex; i++) {
            calendarGrid.insertAdjacentHTML("beforeend", `<div class="calendar-day-cell blank"></div>`);
        }

        for (let day = 1; day <= totalDaysInMonth; day++) {
            const dateStringKey = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
            const isBlocked = blockedDates.includes(dateStringKey);

            let cellClass = "calendar-day-cell text-center p-2 text-white position-relative border border-secondary border-opacity-10";
            if (isBlocked) {
                cellClass += " bg-danger bg-opacity-25 text-danger border-danger fw-bold cursor-pointer";
            }

            const cellHtml = `
                <div class="${cellClass}" ${isBlocked ? `onclick="showCalendarBookingDetails('${dateStringKey}')"` : ''}>
                    <span>${day}</span>
                    ${isBlocked ? `<span class="position-absolute bottom-0 start-50 translate-middle-x mb-1 bg-danger rounded-circle" style="width: 5px; height: 5px;"></span>` : ''}
                </div>`;
                
            calendarGrid.insertAdjacentHTML("beforeend", cellHtml);
        }
    } catch (err) {
        console.error("Availability matrix array dynamic construction failure:", err);
    }
}

window.showCalendarBookingDetails = async function(dateString) {
    try {
        const booking = await ApiService.getBookingDetailsByDate(dateString);
        document.getElementById("modal-name").innerText = booking.customer_name;
        document.getElementById("modal-phone").innerText = booking.phone;
        document.getElementById("modal-email").innerText = booking.email;
        document.getElementById("modal-date").innerText = booking.event_date;
        document.getElementById("modal-venue").innerText = booking.venue_type;
        document.getElementById("modal-status").innerText = booking.booking_status.toUpperCase();
        
        const bModal = new bootstrap.Modal(document.getElementById('bookingModal'));
        bModal.show();
    } catch (err) {
        showModernPopup(`Failed to fetch allocation log profile metadata: ${err.message}`, '', 'error');
    }
};

window.changeMonth = function(direction) {
    currentCalendarDate.setMonth(currentCalendarDate.getMonth() + direction);
    loadDashboardCalendar(); 
};

// =========================================================================
// 5. PRODUCTION ASSET PIPELINE (DASHBOARD GALLERY MODULE LOGIC)
// =========================================================================
async function loadAdminGalleryManager() {
    const displayGrid = document.getElementById("admin-gallery-display-grid");
    if (!displayGrid) return;

    try {
        const assets = await ApiService.getGalleryItems();
        displayGrid.innerHTML = ""; 

        if (assets.length === 0) {
            displayGrid.innerHTML = `<div class="col-12 text-center text-muted py-4"><p>No media streams found in backend mapping index references.</p></div>`;
            return;
        }

        assets.forEach(item => {
           const fileUrl = `https://banagar-associates-crm.onrender.com${item.media_url}`;
            const mediaTemplate = item.media_type === "image" 
                ? `<img src="${fileUrl}" alt="Gallery Asset" class="img-fluid" style="object-fit: cover; height: 100%; width: 100%;">` 
                : `<video src="${fileUrl}" muted class="w-100" style="object-fit: cover; height: 100%;"></video>`;

            const elementCard = `
                <div class="col-md-4 col-lg-3">
                    <div class="stat-card p-0 overflow-hidden gallery-admin-card h-100" style="background: #1b2333; border: 1px solid rgba(255,255,255,0.05);">
                        <div style="height: 160px; overflow: hidden; background: #000;" class="d-flex align-items-center justify-content-center">
                            ${mediaTemplate}
                        </div>
                        <div class="p-3">
                            <div class="d-flex justify-content-between mb-2">
                                <span class="badge bg-primary text-capitalize">${item.media_type}</span>
                                <span class="badge bg-secondary">${item.venue_category}</span>
                            </div>
                            <h6 class="text-white fs-7 mb-1 text-truncate">${item.description || 'No Description Parameters'}</h6>
                            <div class="d-flex justify-content-end mt-3">
                                <button class="btn-icon cancel" style="background: none; border: none; color: #dc3545;" onclick="purgeGalleryMediaItem(${item.id})">
                                    <i class="bi bi-trash"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>`;
            displayGrid.insertAdjacentHTML("beforeend", elementCard);
        });
    } catch (err) {
        console.error("Gallery management runtime grid rendering aborted:", err);
    }
}

async function handleMediaAssetUpload(e) {
    e.preventDefault();
    const uploadBtn = document.getElementById("btn-upload-media");
    const fileSelector = document.getElementById("gallery-file-input");

    if (!fileSelector.files || fileSelector.files.length === 0) {
        showModernPopup("Please specify a local file stream reference first before publishing.", '', 'warning');
        return;
    }

    const formData = new FormData();
    formData.append("file", fileSelector.files[0]);
    formData.append("venue_category", document.getElementById("gallery-venue-category").value);
    formData.append("media_type", document.getElementById("gallery-media-type").value);
    formData.append("description", document.getElementById("gallery-description").value.trim());

    try {
        if (uploadBtn) {
            uploadBtn.disabled = true;
            uploadBtn.innerText = "Uploading Media Stream Parameters...";
        }

        await ApiService.uploadGalleryMedia(formData);
        showModernPopup("Upload verification complete! Corporate media asset live on client interfaces.");

        document.getElementById("gallery-upload-form").reset();
        if (document.getElementById("upload-zone-text")) {
            document.getElementById("upload-zone-text").innerText = "Click / Drag to Choose Media";
        }
        loadAdminGalleryManager();
    } catch (err) {
        showModernPopup(`Media Stream Pipe Interrupted: ${err.message}`, '', 'error');
    } finally {
        if (uploadBtn) {
            uploadBtn.disabled = false;
            uploadBtn.innerText = "UPLOAD & PUBLISH";
        }
    }
}

window.purgeGalleryMediaItem = async function(id) {
    if (!confirm("Permanently discard tracking configuration maps and storage binary contents for this media file?")) return;
    try {
        await ApiService.deleteGalleryMedia(id);
        showModernPopup("Target asset file structure systematically deleted.");
        loadAdminGalleryManager(); 
    } catch (err) {
        showModernPopup(`Purge process routine instance aborted: ${err.message}`, '', 'error');
    }
};

// =========================================================================
// 6. GLOBAL RUNTIME STATE SYNCHRONIZERS (SECURE)
// =========================================================================
window.updateBookingStatus = async function(bookingId, newStatus) {
    // 1. Replace default confirm() with modern modal
    const result = await Swal.fire({
        title: 'Update Status',
        text: `Are you sure you want to mark Booking #${bookingId} as ${newStatus}?`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Yes, update',
        cancelButtonText: 'Cancel',
        background: '#141923', // Your dark theme background
        color: '#ffffff',
        confirmButtonColor: '#0d6efd',
        cancelButtonColor: '#6c757d'
    });

    // 2. Only proceed if user clicked "Yes"
    if (result.isConfirmed) {
        try {
            await ApiService.updateBookingStatus(bookingId, { booking_status: newStatus });
            
            // Success notification using your Toast system
            showToast(`Booking #${bookingId} updated to ${newStatus}`, "success");
            
            // Refresh dashboard
            loadMasterBookingsTable(); 
            loadDashboardAnalytics();
            loadDashboardCalendar();
            
        } catch (error) {
            // Error handling using your modern popup
            Swal.fire({
                title: 'Error',
                text: `Failed to update database: ${error.message}`,
                icon: 'error',
                background: '#141923',
                color: '#ffffff',
                confirmButtonColor: '#dc3545'
            });
        }
    }
};

window.toggleQueryStatus = async function(queryId) {
    try {
        await ApiService.toggleQueryContactStatus(queryId);
        
        // 1. Success feedback that matches your UI theme
        showToast("Lead status successfully updated", "success");
        
        // 2. Refresh the table so the new status appears
        loadCustomerQueriesTable(); 
        
    } catch (err) {
        // 3. Error feedback that matches your UI theme
        console.error("Failed to toggle message state:", err);
        showModernPopup("Error", "Could not update lead status. Please try again.", "error");
    }
};

function exportBookingsToCSV() {
    // 1. Get the dates from the inputs inside your dropdown
    const startDate = document.getElementById("export-start").value;
    const endDate = document.getElementById("export-end").value;

    if (!window.globalBookings || window.globalBookings.length === 0) {
        showToast("No data available to export!", "error");
        return;
    }

    // 2. Filter logic: If dates are provided, filter; otherwise, export all
    let filteredData = window.globalBookings;
    if (startDate && endDate) {
        filteredData = window.globalBookings.filter(b => {
            return b.event_date >= startDate && b.event_date <= endDate;
        });
    }

    if (filteredData.length === 0) {
        showToast("No bookings found in this range!", "error");
        return;
    }

    // 3. Prepare CSV Content
    const headers = ["ID", "Client", "Email", "Phone", "Venue", "Event Type", "Date", "Amount Paid", "Total", "Status"];
    const csvRows = filteredData.map(b => [
        b.id,
        `"${b.customer_name}"`, // Added quotes to handle names with spaces/commas
        b.email,
        b.phone,
        b.venue_type,
        b.event_type,
        b.event_date,
        b.advance_paid,
        b.total_amount,
        b.booking_status
    ]);

    const csvString = [headers.join(","), ...csvRows.map(r => r.join(","))].join("\n");

    // 4. Trigger Download
    const blob = new Blob([csvString], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.setAttribute("href", url);
    a.setAttribute("download", `Bookings_Export_${new Date().toLocaleDateString()}.csv`);
    a.click();
    
    showToast(`Exported ${filteredData.length} bookings successfully!`, "success");
}


function showModernPopup(title, text, icon = 'success') {
    return Swal.fire({
        title: title,
        text: text,
        icon: icon,
        confirmButtonText: 'OK',
        background: '#141923', // Your dark theme background
        color: '#ffffff',      // White text
        backdrop: 'rgba(0,0,0,0.6)',
        confirmButtonColor: '#0d6efd' // Bootstrap Primary blue
    });
}

function showToast(message, type = "success") {
    const container = document.getElementById("toast-container");
    if (!container) return; // Guard clause
    
    const toast = document.createElement("div");
    toast.className = `toast-card ${type === 'success' ? 'toast-success' : 'toast-error'}`;
    toast.innerHTML = `<i class="bi ${type === 'success' ? 'bi-check-circle-fill' : 'bi-exclamation-triangle-fill'}"></i> <span>${message}</span>`;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 500);
    }, 3000);
}

// completed bookings

async function loadCompletedBookingsTable() {
    const tableBody = document.getElementById("completed-bookings-rows");
    if (!tableBody) return;

    try {
        // Grab your explicit security token context from storage
        const myToken = localStorage.getItem('admin_token'); 
        
        // 1. Direct call explicitly pointing to your live Render server pipeline
        const response = await fetch("https://banagar-associates-crm.onrender.com/api/admin/bookings", {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${myToken}`
            }
        });

        if (!response.ok) throw new Error("Unauthorized security context execution.");
        const allBookings = await response.json();

        // 2. Filter data array down to only 'Completed' records
        const completedBookings = allBookings.filter(b => b.booking_status === "Completed");

        tableBody.innerHTML = ""; 

        if (completedBookings.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="10" class="text-center text-muted py-5"><i class="bi bi-inbox fs-3 d-block mb-2 opacity-50"></i>No completed bookings on record yet.</td></tr>`;
            return;
        }

        // 3. Render loop using filtered array structure context maps
        completedBookings.forEach(b => {
            const eventDate = b.event_date ? new Date(b.event_date).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) : 'N/A';
            const createdDate = b.created_at ? new Date(b.created_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) : 'N/A';
            const requests = b.special_requests ? b.special_requests : '<span class="text-muted fst-italic">None</span>';

            const rowHtml = `
                <tr>
                    <td class="ps-4 text-info fw-medium">#${b.id}</td>
                    <td>
                        <strong class="text-white d-block">${b.customer_name}</strong>
                        <span class="text-muted fs-8 d-block"><i class="bi bi-telephone text-secondary me-1"></i>${b.phone}</span>
                        <span class="text-muted fs-8"><i class="bi bi-envelope text-secondary me-1"></i>${b.email || 'N/A'}</span>
                    </td>
                    <td>
                        <span class="text-white d-block">${b.venue_type}</span>
                        <span class="text-muted fs-8">${b.event_type || 'N/A'}</span>
                    </td>
                    <td class="text-white">${eventDate}</td>
                    <td class="text-white">${b.guest_count || '0'}</td>
                    <td class="text-light fs-8" style="max-width: 150px; white-space: normal;">${requests}</td>
                    <td>
                        <div class="fs-8">
                            <span class="text-muted">Total:</span> <strong class="text-white">₹${b.total_amount?.toLocaleString('en-IN') || '0'}</strong><br>
                            <span class="text-muted">Adv:</span> <span class="text-warning">₹${b.advance_paid?.toLocaleString('en-IN') || '0'}</span><br>
                            <span class="text-muted">Bal:</span> <span class="text-danger">₹${b.balance_left?.toLocaleString('en-IN') || '0'}</span>
                        </div>
                    </td>
                    <td>
                        <span class="badge ${b.payment_status === 'Paid' ? 'bg-success' : 'bg-warning'} bg-opacity-10 border ${b.payment_status === 'Paid' ? 'border-success text-success' : 'border-warning text-warning'} border-opacity-25 px-2 py-1 fs-8">
                            ${b.payment_status || 'Pending'}
                        </span>
                    </td>
                    <td>
                        <span class="badge bg-success bg-opacity-10 text-success border border-success border-opacity-25 px-3 py-2 rounded-1 tracking-wide fs-8">
                            <i class="bi bi-check2-all me-1"></i> ${b.booking_status}
                        </span>
                    </td>
                    <td class="pe-4 text-end text-muted fs-8">${createdDate}</td>
                </tr>`;
            tableBody.insertAdjacentHTML("beforeend", rowHtml);
        });
    } catch (err) {
        console.error("Error loading completed bookings:", err);
        tableBody.innerHTML = `<tr><td colspan="10" class="text-center text-danger py-5"><i class="bi bi-exclamation-triangle me-2"></i>Database connection failed. Please ensure you are logged in securely.</td></tr>`;
    }
}

// In your admin.js
async function exportMonthlyBookingsToCSV() {
    const monthInput = document.getElementById("export-month-completed").value; // Format: "YYYY-MM"
    
    if (!monthInput) {
        alert("Please select a month and year first.");
        return;
    }

    try {
        const myToken = localStorage.getItem('admin_token'); 
        const response = await fetch(`/api/admin/bookings`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${myToken}`
            }
        });

        if (!response.ok) throw new Error("Failed to fetch data from server");
        const allBookings = await response.json();

        const filteredBookings = allBookings.filter(b => {
            if (!b.event_date) return false;
           return b.event_date.startsWith(monthInput) && b.booking_status === "Completed";
        });

        if (filteredBookings.length === 0) {
            alert(`No bookings found on record for ${monthInput}.`);
            return;
        }

        const headers = ["Booking ID", "Client Name", "Phone", "Email", "Venue", "Event Type", "Event Date", "Guests", "Total Amount (INR)", "Advance Paid", "Balance Left", "Payment Status", "Booking Status"];
        
        const csvRows = [];
        csvRows.push(headers.join(","));

        filteredBookings.forEach(b => {
            const row = [
                b.id,
                `"${b.customer_name || 'N/A'}"`,
                b.phone || '',
                b.email || '',
                `"${b.venue_type || ''}"`,
                `"${b.event_type || ''}"`,
                b.event_date || '',
                b.guest_count || 0,
                b.total_amount || 0,
                b.advance_paid || 0,
                b.balance_left || 0,
                b.payment_status || 'Pending',
                b.booking_status || ''
            ];
            csvRows.push(row.join(","));
        });

        const csvString = csvRows.join("\n");
        const blob = new Blob([csvString], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement("a");
        
        link.href = URL.createObjectURL(blob);
        link.download = `Banagar_Bookings_${monthInput}.csv`; 
        link.style.display = 'none';
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

    } catch (error) {
        console.error("Export Error:", error);
        alert("Export failed. Please ensure you are logged in securely.");
    }
}

async function calculateSelectedMonthRevenue() {
    const monthInput = document.getElementById("export-month").value; // Format: "YYYY-MM"
    const badge = document.getElementById("monthly-revenue-badge");
    const totalDisplay = document.getElementById("selected-month-total");

    if (!monthInput) {
        badge.classList.add("d-none");
        return;
    }

    try {
        const myToken = localStorage.getItem('admin_token'); 
        const response = await fetch(`/api/admin/bookings`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${myToken}`
            }
        });

        if (!response.ok) throw new Error("Failed to load records");
        const allBookings = await response.json();

        // Filter: Only look at 'Completed' statuses for the selected Year-Month
        const targetMonthBookings = allBookings.filter(b => 
            b.event_date && 
            b.event_date.startsWith(monthInput) && 
            b.booking_status === "Completed"
        );

        // Sum up the total revenue
        const totalRevenue = targetMonthBookings.reduce((sum, current) => {
            return sum + (parseFloat(current.total_amount) || 0);
        }, 0);

        // Render to the user with slick formatting
        totalDisplay.innerText = `₹${totalRevenue.toLocaleString('en-IN')}`;
        badge.classList.remove("d-none"); // Make it visible

    } catch (error) {
        console.error("Error calculating month-wise metrics:", error);
        totalDisplay.innerText = "Error loading";
        badge.classList.remove("d-none");
    }
}

