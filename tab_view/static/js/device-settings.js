document.addEventListener('DOMContentLoaded', function() {
    // --- MEDIA PICKER LOGIC ---
    const mediaPreview = document.getElementById('defaultMediaPreview');
    const mediaSelect = document.getElementById('defaultMediaSelect');
    const modalEl = document.getElementById('mediaPickerModal');

    function renderPreview(mediaId) {
        if (!mediaId || !window.mediaList) return;

        const media = window.mediaList.find(m => m.id == mediaId);
        if (!media) return;

        let previewHtml = '';
        if (media.media_type === 'image') {
            previewHtml = `<img src="/static/uploads/${media.filename}" alt="Selected Media" class="img-fluid rounded-3 shadow-sm" style="max-height: 200px; object-fit: contain;">`;
        } else {
            previewHtml = `<video src="/static/uploads/${media.filename}" class="img-fluid rounded-3 shadow-sm" style="max-height: 200px; object-fit: contain;" autoplay loop muted playsinline></video>`;
        }

        if (mediaPreview) {
            mediaPreview.innerHTML = previewHtml;
            mediaPreview.style.border = 'none';
            mediaPreview.style.backgroundColor = 'transparent';
        }
    }

    if (mediaPreview && modalEl) {
        const mediaPickerModal = new bootstrap.Modal(modalEl);

        if (window.currentDeviceMediaId) {
            renderPreview(window.currentDeviceMediaId);
        }

        // Open modal on preview click
        mediaPreview.addEventListener('click', function() {
            mediaPickerModal.show();
        });

        // Handle media selection
        document.querySelectorAll('.media-picker-item').forEach(item => {
            item.addEventListener('click', function(e) {
                e.preventDefault();

                const mediaId = this.dataset.mediaId;

                // Update hidden input for form submission
                if (mediaSelect) {
                    mediaSelect.value = mediaId;
                }

                // Update styling to show selection
                document.querySelectorAll('.media-picker-item').forEach(i => i.classList.remove('border-primary', 'border-2'));
                this.classList.add('border-primary', 'border-2');

                // Update the preview box
                renderPreview(mediaId);

                // Close modal
                mediaPickerModal.hide();
            });
        });
    }

    // --- TAG FILTERING LOGIC ---
    const tagCheckboxes = document.querySelectorAll('.tag-filter-checkbox');
    const mediaFilterItems = document.querySelectorAll('.media-filter-item');

    if (tagCheckboxes.length > 0 && mediaFilterItems.length > 0) {
        const allCheckbox = document.getElementById('tag-all');

        tagCheckboxes.forEach(cb => {
            cb.addEventListener('change', function() {
                const isAll = this.dataset.filter === 'all';

                if (isAll && this.checked) {
                    tagCheckboxes.forEach(otherCb => {
                        if (otherCb !== this) otherCb.checked = false;
                    });
                } else if (!isAll && this.checked) {
                    if (allCheckbox) allCheckbox.checked = false;
                } else if (!isAll && !this.checked) {
                    const anyChecked = Array.from(tagCheckboxes).some(c => c.dataset.filter !== 'all' && c.checked);
                    if (!anyChecked && allCheckbox) {
                        allCheckbox.checked = true;
                    }
                }

                if (isAll && !this.checked) {
                     const anyChecked = Array.from(tagCheckboxes).some(c => c.dataset.filter !== 'all' && c.checked);
                     if (!anyChecked) this.checked = true;
                }

                const activeFilters = Array.from(tagCheckboxes)
                    .filter(c => c.checked)
                    .map(c => c.dataset.filter);

                mediaFilterItems.forEach(item => {
                    const itemTagId = item.dataset.tagId ? item.dataset.tagId.toString() : "";
                    if (activeFilters.includes('all') || activeFilters.includes(itemTagId)) {
                        item.style.display = '';
                    } else {
                        item.style.display = 'none';
                    }
                });
            });
        });
    }
});
