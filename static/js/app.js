/**
 * PocketSmart AI - Client-side Interactive Logic & Enhancements
 */

document.addEventListener("DOMContentLoaded", () => {
    // 1. Mobile Menu Toggle
    const mobileToggle = document.getElementById("mobileMenuToggle");
    const mainNav = document.getElementById("mainNav");

    if (mobileToggle && mainNav) {
        mobileToggle.addEventListener("click", () => {
            mainNav.classList.toggle("open");
            const icon = mobileToggle.querySelector("i");
            if (icon) {
                if (mainNav.classList.contains("open")) {
                    icon.classList.remove("fa-bars");
                    icon.classList.add("fa-xmark");
                } else {
                    icon.classList.remove("fa-xmark");
                    icon.classList.add("fa-bars");
                }
            }
        });
    }

    // 2. Global Loading Overlay on Planner Forms
    const plannerForms = document.querySelectorAll(".planner-form");
    const loadingOverlay = document.getElementById("loadingOverlay");
    const loadingTitle = document.getElementById("loadingTitle");
    const loadingSubtitle = document.getElementById("loadingSubtitle");

    plannerForms.forEach(form => {
        form.addEventListener("submit", (e) => {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Processing Plan...';
            }

            if (loadingOverlay) {
                const plannerType = form.dataset.plannerType || "budget";
                if (plannerType === "home") {
                    loadingTitle.textContent = "Analyzing Rooms & Calculating Interior Budgets...";
                    loadingSubtitle.textContent = "Sourcing optimized fixtures from IKEA, Amazon & Flipkart...";
                } else if (plannerType === "party") {
                    loadingTitle.textContent = "Planning Event & Allocating Category Budgets...";
                    loadingSubtitle.textContent = "Matching catering, venue, and decor vendors on Swiggy, Zomato & OYO...";
                } else if (plannerType === "jewelry") {
                    loadingTitle.textContent = "Analyzing Outfit Aesthetics & Matching Jewelry...";
                    loadingSubtitle.textContent = "Consulting Gemini multimodal stylist for colors, metal coordination & pricing...";
                }
                loadingOverlay.style.display = "flex";
            }
        });
    });

    // 3. Outfit Image Upload Drag & Drop and Preview (Jewelry Planner)
    const dropzone = document.getElementById("outfitDropzone");
    const fileInput = document.getElementById("outfitImageInput");
    const previewWrapper = document.getElementById("imagePreviewWrapper");
    const previewImg = document.getElementById("imagePreview");
    const removeBtn = document.getElementById("removeImageBtn");

    if (dropzone && fileInput) {
        // Trigger file select on click
        dropzone.addEventListener("click", () => fileInput.click());

        // Drag & Drop events
        ['dragenter', 'dragover'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.add("drag-over");
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.remove("drag-over");
            }, false);
        });

        dropzone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files.length > 0) {
                fileInput.files = files;
                handleImagePreview(files[0]);
            }
        });

        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) {
                handleImagePreview(fileInput.files[0]);
            }
        });

        if (removeBtn) {
            removeBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                fileInput.value = "";
                if (previewWrapper) previewWrapper.style.display = "none";
                if (dropzone) dropzone.style.display = "block";
            });
        }
    }

    function handleImagePreview(file) {
        if (!file.type.startsWith('image/')) {
            alert('Please select a valid image file (JPG, PNG, or WEBP).');
            return;
        }
        const reader = new FileReader();
        reader.onload = (e) => {
            if (previewImg) previewImg.src = e.target.result;
            if (previewWrapper) previewWrapper.style.display = "block";
            if (dropzone) dropzone.style.display = "none";
        };
        reader.readAsDataURL(file);
    }

    // 4. Sliders Sync with Badges
    const syncSliders = document.querySelectorAll('input[type="range"][data-badge-target]');
    syncSliders.forEach(slider => {
        const targetId = slider.getAttribute('data-badge-target');
        const badge = document.getElementById(targetId);
        if (badge) {
            slider.addEventListener('input', () => {
                badge.textContent = slider.value;
            });
        }
    });

    // 5. Print Plan Button
    const printBtn = document.getElementById("printPlanBtn");
    if (printBtn) {
        printBtn.addEventListener("click", () => {
            window.print();
        });
    }
});
