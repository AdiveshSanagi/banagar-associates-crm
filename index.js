// Simple Intersection Observer to activate animations dynamically as user scrolls down
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if(entry.isIntersecting) {
            entry.target.classList.add('animate__animated', entry.target.dataset.animate);
            observer.unobserve(entry.target);
        }
    });
}, { threshold: 0.1 });

document.querySelectorAll('[data-animate]').forEach(el => observer.observe(el));

// Navbar transparent-to-solid transition on scroll
window.addEventListener('scroll', function() {
    const nav = document.querySelector('.navbar');
    if (window.scrollY > 50) {
        nav.classList.add('bg-dark-solid', 'shadow-lg');
    } else {
        nav.classList.remove('bg-dark-solid', 'shadow-lg');
    }
});

// Live Card Category Filtering Logic
document.addEventListener("DOMContentLoaded", function () {
    const filterButtons = document.querySelectorAll("#venue-filter-controls .btn-filter");
    const portfolioItems = document.querySelectorAll("#filterable-venue-grid .venue-portfolio-item");

    filterButtons.forEach(button => {
        button.addEventListener("click", function () {
            // Remove active style from old button, assign to clicked button
            document.querySelector(".active-filter").classList.remove("active-filter");
            this.classList.add("active-filter");

            const filterTarget = this.getAttribute("data-filter");

            portfolioItems.forEach(item => {
                const itemCategory = item.getAttribute("data-category");

                // Check condition if 'all' is selected or if asset type matches selection
                if (filterTarget === "all" || itemCategory === filterTarget) {
                    item.classList.remove("hidden-item");
                    
                    // Trigger a quick clean CSS structural animation entrance trigger
                    setTimeout(() => {
                        item.style.display = "block";
                    }, 10);
                } else {
                    item.classList.add("hidden-item");
                    setTimeout(() => {
                        item.style.display = "none";
                    }, 400); // Matches CSS transition duration limits cleanly
                }
            });
        });
    });
});


// Live Gallery Asset Format Filter Logic
document.addEventListener("DOMContentLoaded", function () {
    const gFilterButtons = document.querySelectorAll("#gallery-filter-controls .btn-gallery-filter");
    // Note: We use a live node list query below because the grid items will be injected dynamically by the API!

    gFilterButtons.forEach(btn => {
        btn.addEventListener("click", function () {
            // Drop styling state anchor token from old element, assign to click target
            document.querySelector(".active-g-filter").classList.remove("active-g-filter");
            this.classList.add("active-g-filter");

            const targetedCategory = this.getAttribute("data-gfilter");
            
            // Re-select items here to ensure we grab the dynamically injected ones
            const gGridItems = document.querySelectorAll("#filterable-gallery-grid .gallery-matrix-item");

            gGridItems.forEach(item => {
                const itemFormatGroup = item.getAttribute("data-gcat");

                if (targetedCategory === "all" || itemFormatGroup === targetedCategory) {
                    item.classList.remove("hide-asset");
                    setTimeout(() => {
                        item.style.display = "block";
                    }, 5);
                } else {
                    item.classList.add("hide-asset");
                    setTimeout(() => {
                        item.style.display = "none";
                    }, 350);
                }
            });
        });
    });
});

// Close the hamburger menu on mobile after clicking a link
document.addEventListener("DOMContentLoaded", function () {
    const mobileMenu = document.querySelector(".navbar-toggler");
    const navLinks = document.querySelectorAll(".nav-link");

    navLinks.forEach(link => {
        link.addEventListener("click", function () {
            if (window.innerWidth < 992) {
                mobileMenu.click();
            }
        });
    });
});

// =========================================================================
// PUBLIC API INTEGRATIONS (Contact Form & Dynamic Gallery)
// =========================================================================
document.addEventListener("DOMContentLoaded", () => {
    
    // 1. DYNAMIC GALLERY FETCH ENGINE (Solves the broken image issue)
    async function fetchAndRenderGallery() {
        const galleryGrid = document.getElementById("filterable-gallery-grid");
        if (!galleryGrid) return; // Exit if we are on a page without a gallery

        try {
            const assets = await ApiService.getGalleryItems();
            galleryGrid.innerHTML = ""; // Wipe any hardcoded HTML

            if (assets.length === 0) {
                galleryGrid.innerHTML = `<div class="col-12 text-center text-muted"><p>Gallery is currently being updated. Check back soon!</p></div>`;
                return;
            }

            assets.forEach(item => {
                // THE FIX: Prepend the backend localhost URL to the database path
               const fullMediaUrl = item.media_url.startsWith("http") 
                    ? item.media_url 
                    : `https://banagar-associates-crm.onrender.com${item.media_url}`;
                
                // Map backend media_type to frontend filter categories
                const filterCategory = item.media_type === "image" ? "photos" : "videos";

                let mediaHtml = '';
                if (item.media_type === "image") {
                    mediaHtml = `<img src="${fullMediaUrl}" alt="${item.description || 'Banagar Associates Gallery'}" class="img-fluid w-100 h-100" style="object-fit: cover;">`;
                } else if (item.media_type === "video") {
                    mediaHtml = `<video src="${fullMediaUrl}" class="img-fluid w-100 h-100" style="object-fit: cover;" controls></video>`;
                }

                // Construct the HTML for each gallery card
                const gridItem = `
                    <div class="col-sm-6 col-lg-4 gallery-matrix-item" data-gcat="${filterCategory}">
                        <div class="position-relative overflow-hidden shadow-sm" style="height: 300px; border-radius: 8px; background: #000;">
                            ${mediaHtml}
                            <div class="position-absolute bottom-0 start-0 w-100 p-3" style="background: linear-gradient(transparent, rgba(0,0,0,0.8));">
                                <span class="badge bg-primary mb-1">${item.venue_category}</span>
                                ${item.description ? `<p class="text-white fs-7 mb-0 text-truncate">${item.description}</p>` : ''}
                            </div>
                        </div>
                    </div>
                `;
                
                galleryGrid.insertAdjacentHTML("beforeend", gridItem);
            });

        } catch (err) {
            console.error("Failed to sync live gallery:", err);
        }
    }

    // Fire the gallery fetch immediately
    fetchAndRenderGallery();

    // 2. CONTACT FORM PIPELINE
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
                submitButton.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> <span>SENDING...</span>`;
                
                await ApiService.submitEnquiry(payload);
                
                alert("Thank you! Your inquiry has been submitted successfully to our database.");
                inquiryForm.reset(); 
                
            } catch (err) {
                alert(`Submission error: ${err.message}`);
            } finally {
                submitButton.disabled = false;
                submitButton.innerHTML = originalButtonText;
            }
        });
    }
});
