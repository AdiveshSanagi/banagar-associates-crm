// =========================================================================
// BANAGAR ASSOCIATES - MASTER BACKEND GATEWAY CONNECTOR
// Place this file at the root of your project: /api-integration.js
// =========================================================================

// Make sure it has /api at the end, but NO trailing slash (/)
const BASE_URL = "https://banagar-associates-crm-production.up.railway.app/api";

const ApiService = {
    /**
     * Core Request Wrapper
     * Automatically handles JSON headers and injects secure Admin JWT Tokens
     */
    async request(endpoint, options = {}) {
        const token = localStorage.getItem("admin_token");
        const headers = { ...options.headers };

        // SECURITY FIX: Exclude both FormData (files) AND URLSearchParams (login) from being forced to JSON
        if (!(options.body instanceof FormData) && !(options.body instanceof URLSearchParams)) {
            headers["Content-Type"] = "application/json";
        }
        
        // Securely inject token if admin is currently authenticated
        if (token) {
            headers["Authorization"] = `Bearer ${token}`;
        }

        const config = { ...options, headers };
        try {
            const response = await fetch(`${BASE_URL}${endpoint}`, config);
            
            // SECURITY KICK-OUT: If token is expired/invalid, auto-logout (unless we are actively trying to log in)
            if (response.status === 401 && !endpoint.includes("/login")) {
                this.logout();
                throw new Error("Session expired. Please log in again.");
            }

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP Error Status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`System API Routing Error [${endpoint}]:`, error.message);
            throw error;
        }
    },

    // =====================================================================
    // 1. PUBLIC CUSTOMER METHOD ENDPOINTS
    // =====================================================================

    async getBookedDates() {
        return this.request("/public/booked-dates", { method: "GET" });
    },

    async submitBooking(bookingData) {
        return this.request("/public/bookings", {
            method: "POST",
            body: JSON.stringify(bookingData)
        });
    },

    async submitEnquiry(enquiryData) {
        return this.request("/public/queries", {
            method: "POST",
            body: JSON.stringify(enquiryData)
        });
    },

    async getGalleryItems(filters = {}) {
        const params = new URLSearchParams();
        if (filters.venue_category) params.append("venue_category", filters.venue_category);
        if (filters.media_type) params.append("media_type", filters.media_type);
        if (filters.limit) params.append("limit", filters.limit);
        
        const queryStr = params.toString() ? `?${params.toString()}` : "";
        return this.request(`/public/gallery${queryStr}`, { method: "GET" });
    },

    // =====================================================================
    // 2. ADMIN SECURE DASHBOARD ENDPOINTS (Protected by JWT Security Guards)
    // =====================================================================

    /**
     * Authenticates admin email/password against backend hash, sets local security token
     */
    async adminLogin(email, password) {
        // MATCHES YOUR FASTAPI PYDANTIC MODEL PERFECTLY
        const data = await this.request("/admin/login", { 
            method: "POST",
            body: JSON.stringify({ email: email, password: password }) // Standard JSON format!
        });
        
        if (data.access_token) {
            localStorage.setItem("admin_token", data.access_token);
        }
        return data;
    },
    /**
     * Top Cards: Live mathematical synchronization data blocks
     */
    async getDashboardStats() {
        return this.request("/admin/dashboard/stats", { method: "GET" });
    },

    /**
     * Master Booking Matrix: Loads full historical customer entries
     */
    async getAllBookings() {
        return this.request("/admin/bookings", { method: "GET" });
    },

    /**
     * Overview Row: Filters customer bookings matching the active current calendar month
     */
    async getRecentBookings() {
        return this.request("/admin/bookings/recent", { method: "GET" });
    },

    /**
     * Actions Column: Allows operators to modify, confirm, or explicitly cancel user slots
     */
    async updateBookingStatus(bookingId, statusUpdate) {
        return this.request(`/admin/bookings/${bookingId}`, {
            method: "PUT",
            body: JSON.stringify(statusUpdate)
        });
    },

    /**
     * Interactive Calendar Node: Clicking a blocked section pulls the full consumer profile card details
     */
    async getBookingDetailsByDate(dateString) {
        return this.request(`/admin/bookings/date/${dateString}`, { method: "GET" });
    },

    /**
     * Lead Tracking: Gathers contact form inquiries
     */
    async getAllQueries() {
        return this.request("/admin/queries", { method: "GET" });
    },

    /**
     * Core Checkbox Toggle: Switches lead validation states between 'Contacted' and 'Not Contacted'
     */
    async toggleQueryContactStatus(queryId) {
        return this.request(`/admin/queries/${queryId}/status`, { method: "PATCH" });
    },

    /**
     * Content Upload: Pipes drag-and-drop media streams ensuring format restrictions are evaluated
     */
    async uploadGalleryMedia(formData) {
        return this.request("/admin/gallery", {
            method: "POST",
            body: formData
        });
    },

    async getCompletedBookings() {
    // 👇 Grabbing the exact key you found! 👇
    const myToken = localStorage.getItem('admin_token'); 

    const response = await fetch(`/api/admin/bookings/completed`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${myToken}` // Securely passing it to Python
        }
    });

    if (!response.ok) {
        throw new Error("Failed to load completed bookings history");
    }
    return response.json();
},
    /**
     * Password updation by admin
     */
    async updateAdminPassword(passwordData) {
        return await this.request("/admin/update-password", {
            method: "PUT",
            body: JSON.stringify(passwordData)
        });
    },

    /**
     * System Purge: Removes media entries from storage maps and database references entirely
     */
    async deleteGalleryMedia(itemId) {
        return this.request(`/admin/gallery/${itemId}`, { method: "DELETE" });
    },
    
    /**
     * Clears administrative login credentials token and kicks user back to login page
     */
    logout() {
        localStorage.removeItem("admin_token");
        window.location.href = "adminlogin.html"; // <--- CHANGE THIS LINE
    }
};

