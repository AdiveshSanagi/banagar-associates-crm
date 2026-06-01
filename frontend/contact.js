// =========================================================================
// BANAGAR ASSOCIATES - PUBLIC CONTACT MODULE
// =========================================================================

// --- 1. CINEMATIC UI HELPER FUNCTIONS ---
function showToast(message, type = "success") {
    const container = document.getElementById("toast-container");
    if (!container) return;
    
    const toast = document.createElement("div");
    toast.className = `toast-card ${type === 'success' ? 'toast-success' : 'toast-error'}`;
    toast.innerHTML = `<i class="bi ${type === 'success' ? 'bi-check-circle-fill' : 'bi-exclamation-triangle-fill'}"></i> <span>${message}</span>`;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 500);
    }, 3000);
}

function showModernPopup(title, text, icon = 'success') {
    Swal.fire({
        title: title,
        text: text,
        icon: icon,
        background: '#141923',
        color: '#ffffff',
        confirmButtonColor: '#0d6efd'
    });
}

// --- 2. FORM SUBMISSION ENGINE ---
document.addEventListener("DOMContentLoaded", () => {
    const inquiryForm = document.getElementById("inquiry-form");
    
    if (inquiryForm) {
        inquiryForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            
            const submitButton = inquiryForm.querySelector("button[type='submit']");
            const originalButtonText = submitButton.innerHTML;

            const payload = {
                name: document.getElementById("user_name").value.trim(),
                phone: document.getElementById("user_phone").value.trim(),
                email: document.getElementById("user_email").value.trim() || null,
                event_date: document.getElementById("event_date").value || new Date().toISOString().split('T')[0],
                message: document.getElementById("user_message").value.trim()
            };
            
            try {
                submitButton.disabled = true;
                submitButton.innerHTML = `<span>SENDING...</span>`;
                
                // Ensure ApiService is available globally
                await ApiService.submitEnquiry(payload);
                
                showToast("Thank you! Your inquiry has been submitted successfully.", "success");
                inquiryForm.reset();
                
            } catch (err) {
                showModernPopup("Submission Error", err.message, "error");
            } finally {
                submitButton.disabled = false;
                submitButton.innerHTML = originalButtonText;
            }
        });
    }
});