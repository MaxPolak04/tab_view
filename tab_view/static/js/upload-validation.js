document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    const fileInput = document.getElementById('fileInput');
    const errorContainer = document.getElementById('js-error-container');
    const submitBtn = document.getElementById('submitBtn');

    // Safety check in case the script is accidentally loaded elsewhere
    if (!uploadForm || !fileInput || !errorContainer || !submitBtn) return;

    // Set max size in bytes (2GB)
    const MAX_TOTAL_SIZE = 2 * 1024 * 1024 * 1024;

    uploadForm.addEventListener('submit', function(e) {
        // Clear previous errors
        errorContainer.innerHTML = '';
        let totalSize = 0;

        if (fileInput.files.length > 0) {
            for (let i = 0; i < fileInput.files.length; i++) {
                totalSize += fileInput.files[i].size;
            }

            if (totalSize > MAX_TOTAL_SIZE) {
                // Prevent form submission to avoid server crash/Nginx error
                e.preventDefault();

                // Format sizes for readability
                const totalSizeMB = (totalSize / (1024 * 1024)).toFixed(2);
                const maxSizeMB = (MAX_TOTAL_SIZE / (1024 * 1024)).toFixed(0);

                // Inject Bootstrap alert
                const alertHtml = `
                    <div class="alert alert-danger alert-dismissible fade show shadow-sm" role="alert">
                        <strong><i class="bi bi-exclamation-triangle-fill me-2"></i>Upload too large!</strong>
                        You are trying to upload ${totalSizeMB} MB, but the maximum allowed total size is ${maxSizeMB} MB. Please select fewer or smaller files.
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>
                `;
                errorContainer.innerHTML = alertHtml;

                // Scroll to top to ensure user sees the error
                window.scrollTo({ top: 0, behavior: 'smooth' });

                // Reset submit button state if it was disabled
                submitBtn.disabled = false;
            } else {
                // Provide visual feedback that upload is starting
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Uploading...';
            }
        }
    });
});
