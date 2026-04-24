// --- TOOLTIPS AND POPOVERs ---
const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))

const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]')
const popoverList = [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl))

// --- NAVBAR HANDLER ---
const nav = document.querySelector('.navbar-collapse');
if (nav) {
    document.addEventListener('click', (e) => {
        if (nav.classList.contains('show')) {
            nav.classList.remove('show');
        }
    });
}

// --- FORM PROCESSING ---
const mainForm = document.querySelector('form');
if (mainForm) {
    mainForm.addEventListener('submit', function(e) {
        const btn = this.querySelector('button[type="submit"]');
        if (btn) {
            btn.disabled = true;
            btn.innerText = 'Uploading...';
        }
    });
}

// --- FLASH MESSAGES ---
setTimeout(() => {
    document.querySelectorAll('.flash-overlay .alert').forEach(alert => {
        alert.classList.add('fade-out');
        setTimeout(() => alert.remove(), 500);
    });
}, 3000);

// --- THEME MANAGER ---
document.addEventListener('DOMContentLoaded', () => {
    const themeToggle = document.getElementById('theme-toggle');
    const themeIcon = document.getElementById('theme-icon');
    const htmlElement = document.documentElement;

    const savedTheme = localStorage.getItem('theme') || 'light';
    htmlElement.setAttribute('data-bs-theme', savedTheme);

    const updateIcon = (theme) => {
        if (!themeIcon) return;
        if (theme === 'dark') {
            themeIcon.classList.remove('bi-moon-stars-fill');
            themeIcon.classList.add('bi-sun-fill');
        } else {
            themeIcon.classList.remove('bi-sun-fill');
            themeIcon.classList.add('bi-moon-stars-fill');
        }
    };

    updateIcon(savedTheme);

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const currentTheme = htmlElement.getAttribute('data-bs-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

            htmlElement.setAttribute('data-bs-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateIcon(newTheme);
        });
    }
});

document.addEventListener('DOMContentLoaded', function() {

    // --- TAG SELECTION LOGIC ---
    const select = document.getElementById('tagSelect');
    const input = document.getElementById('newTagInput');

    // Only run if these elements exist on the current page
    if (select && input) {
        function updateSelectState() {
            if (input.value.trim().length > 0) {
                select.disabled = true;
                select.value = 0;
                select.classList.add('opacity-50');
            } else {
                select.disabled = false;
                select.classList.remove('opacity-50');
            }
        }

        input.addEventListener('input', updateSelectState);
    }

    // --- FILE SELECTION PREVIEW LOGIC ---
    const fileInput = document.getElementById('fileInput');
    const fileListPreview = document.getElementById('fileListPreview');

    // Only run if these elements exist on the current page
    if (fileInput && fileListPreview) {
        fileInput.addEventListener('change', function() {
            const files = fileInput.files;
            if (files.length === 0) {
                fileListPreview.innerHTML = '';
                return;
            }

            if (files.length === 1) {
                fileListPreview.innerHTML = `<i class="bi bi-check-circle-fill me-1"></i> Selected file: ${files[0].name}`;
            } else {
                fileListPreview.innerHTML = `<i class="bi bi-collection-fill me-1"></i> ${files.length} files selected for upload.`;
            }
        });
    }
});


// YEAR
document.addEventListener('DOMContentLoaded', () => {
    const handleCurrentYear = () => {
        const footerYear = document.querySelector('.current_year');

        if (footerYear) {
            footerYear.innerText = new Date().getFullYear();
        }
    };

    handleCurrentYear();
});

document.addEventListener("DOMContentLoaded", function() {
    const showPasswordCheckbox = document.getElementById("show_password");
    const passwordFields = document.querySelectorAll("input[type='password'], input[data-toggle-password]");

    if (showPasswordCheckbox) {
        showPasswordCheckbox.addEventListener("change", function() {
            const type = this.checked ? "text" : "password";
            passwordFields.forEach(field => {
                field.type = type;
                // Add a custom attribute so we don't lose track of which inputs are password inputs
                field.setAttribute("data-toggle-password", "true");
            });
        });
    }
});
