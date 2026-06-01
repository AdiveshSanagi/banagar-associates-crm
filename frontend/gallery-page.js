// =========================================================================
// BANAGAR ASSOCIATES - HOMEPAGE PORTFOLIO LOGIC (MAX 8 CORES)
// =========================================================================

let homepageCachedMedia = [];

document.addEventListener("DOMContentLoaded", () => {
    initHomepageGallery();
});

async function initHomepageGallery() {
    const grid = document.getElementById("full-portfolio-grid");
    if (!grid) return;

    try {
        const response = await fetch("http://localhost:8000/api/public/gallery");
        if (!response.ok) throw new Error("Database file stream failed.");
        
        const data = await response.json();
        
        // Save globally for seamless tab filtering later
        homepageCachedMedia = data;
        
        // Display the slice array limited strictly to 8 cards max
        renderHomeGalleryCards(homepageCachedMedia.slice(0, 8));

    } catch (err) {
        console.error("Error reading portfolio array:", err);
        grid.innerHTML = `<div class="col-12 text-center text-muted py-4"><p>Visual gallery temporary offline.</p></div>`;
    }
}

function renderHomeGalleryCards(items) {
    const grid = document.getElementById("full-portfolio-grid");
    if (!grid) return;

    grid.innerHTML = "";

    if (items.length === 0) {
        grid.innerHTML = `<div class="col-12 text-center text-muted py-5"><p>No items published by admin yet.</p></div>`;
        return;
    }

    items.forEach(item => {
        const fileUrl = `https://banagar-associates-crm.onrender.com${item.media_url}`;
        
        // Dynamically build content based on file properties
        const mediaTag = item.media_type === "image"
            ? `<img src="${fileUrl}" alt="${item.description}" class="img-fluid gallery-asset" style="object-fit: cover; height: 100%; width: 100%;">`
            : `<video src="${fileUrl}" muted autoplay loop class="w-100" style="object-fit: cover; height: 100%; min-height:220px;"></video>`;

        const badgeTag = item.media_type === "image"
            ? `<span class="badge bg-gold text-dark rounded-0 px-2 py-1 align-self-start"><i class="bi bi-camera me-1"></i> IMAGE</span>`
            : `<span class="badge bg-primary rounded-0 px-2 py-1 align-self-start"><i class="bi bi-play-circle me-1"></i> VIDEO</span>`;

        const cardHtml = `
            <div class="col-sm-6 col-md-4 col-xl-3">
                <div class="gallery-mini-card position-relative overflow-hidden shadow-sm" style="height: 250px; background:#000;">
                    <div class="w-100 h-100 d-flex align-items-center justify-content-center overflow-hidden">
                        ${mediaTag}
                    </div>
                    <div class="gallery-asset-overlay p-3 d-flex flex-column justify-content-between">
                        ${badgeTag}
                        <div>
                            <span class="fs-8 tracking-wider text-gold text-uppercase d-block mb-1">${item.venue_category}</span>
                            <h5 class="h6 text-white font-serif mb-0 text-truncate">${item.description || 'Banagar Luxury Setup'}</h5>
                        </div>
                    </div>
                </div>
            </div>`;
        
        grid.insertAdjacentHTML("beforeend", cardHtml);
    });
}

// Live client side filter loop for homepage tabs (keeps slice at 8 max)
window.filterHomeGallery = function(type, btnElement) {
    const buttons = document.querySelectorAll("#homepage-gallery-filter-controls .btn");
    buttons.forEach(b => b.classList.remove("active-g-filter"));
    if (btnElement) btnElement.classList.add("active-g-filter");

    if (type === "all") {
        renderHomeGalleryCards(homepageCachedMedia.slice(0, 8));
    } else {
        const filtered = homepageCachedMedia.filter(item => item.media_type === type);
        renderHomeGalleryCards(filtered.slice(0, 8));
    }
};
