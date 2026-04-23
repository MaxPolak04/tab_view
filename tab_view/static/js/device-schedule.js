document.addEventListener('DOMContentLoaded', function() {
    const currentDeviceId = window.currentDeviceId;
    let calendar;
    let currentEventId = null;
    let currentPlaylist = [];

    const eventModalEl = document.getElementById('eventModal');
    const eventModal = eventModalEl ? new bootstrap.Modal(eventModalEl) : null;

    const mediaPickerModalEl = document.getElementById('mediaPickerModal');
    const mediaPickerModal = mediaPickerModalEl ? new bootstrap.Modal(mediaPickerModalEl) : null;

    const playlistMediaPickerModalEl = document.getElementById('playlistMediaPickerModal');
    const playlistMediaPickerModal = playlistMediaPickerModalEl ? new bootstrap.Modal(playlistMediaPickerModalEl) : null;

    if (playlistMediaPickerModalEl) {
        playlistMediaPickerModalEl.addEventListener('hidden.bs.modal', function() {
            renderPlaylist();
        });
    }

    // Helper to show errors gracefully
    function showEventError(message) {
        const errorContainer = document.getElementById('eventFormError');
        const errorText = document.getElementById('eventFormErrorText');
        if (errorContainer && errorText) {
            errorText.textContent = message;
            errorContainer.classList.remove('d-none');
            // Scroll to top of modal to ensure error is visible
            document.querySelector('#eventModal .modal-body').scrollTop = 0;
        } else {
            // Fallback
            alert(message);
        }
    }

    function hideEventError() {
        const errorContainer = document.getElementById('eventFormError');
        if (errorContainer) {
            errorContainer.classList.add('d-none');
        }
    }

    // Smart default dates helper
    function getSmartDates(baseDateStr = null) {
        let now = new Date();
        let start = baseDateStr ? new Date(baseDateStr) : new Date();
        start.setHours(now.getHours());

        let minutes = now.getMinutes();
        let remainder = minutes % 5;
        let addMinutes = (5 - remainder) + 5;

        start.setMinutes(minutes + addMinutes);
        start.setSeconds(0);
        start.setMilliseconds(0);

        let end = new Date(start);
        end.setHours(end.getHours() + 1);

        return { start: formatDateTimeLocal(start), end: formatDateTimeLocal(end) };
    }

    const flatpickrConfig = {
        enableTime: true,
        dateFormat: "Y-m-d\\TH:i",
        altInput: true,
        altFormat: "d.m.Y H:i",
        time_24hr: true,
        locale: "pl",
        onReady: function(selectedDates, dateStr, instance) {
            const btnContainer = document.createElement("div");
            btnContainer.className = "d-grid px-2 pb-2 pt-1";
            const btn = document.createElement("button");
            btn.className = "btn btn-primary btn-sm shadow-sm";
            btn.type = "button";
            btn.innerText = "OK";
            btn.addEventListener("click", function() {
                instance.close();
            });
            btnContainer.appendChild(btn);
            instance.calendarContainer.appendChild(btnContainer);
        }
    };

    flatpickr("#eventStart", flatpickrConfig);
    flatpickr("#eventEnd", flatpickrConfig);

    const textOnlySwitch = document.getElementById('eventTextOnly');
    const mediaSection = document.getElementById('mediaSection');

    if (textOnlySwitch && mediaSection) {
        textOnlySwitch.addEventListener('change', function(e) {
            if (e.target.checked) {
                mediaSection.style.display = 'none';
            } else {
                mediaSection.style.display = 'block';
            }
        });
    }

    const calendarEl = document.getElementById('calendar');
    if (calendarEl) {
        calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'dayGridMonth',
            locale: 'pl',
            eventTimeFormat: { hour: '2-digit', minute: '2-digit', hour12: false },
            slotLabelFormat: { hour: '2-digit', minute: '2-digit', hour12: false },
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek,timeGridDay'
            },
            slotMinTime: '06:00:00',
            slotMaxTime: '22:00:00',
            allDaySlot: false,
            editable: true,
            selectable: true,
            selectMirror: true,
            selectOverlap: true,

            events: function(info, successCallback, failureCallback) {
                const params = new URLSearchParams({ device_id: currentDeviceId, start: info.startStr, end: info.endStr });
                fetch(`/api/v1/events/?device_id=${currentDeviceId}`, { credentials: 'same-origin' })
                .then(res => {
                    if (res.status === 401) { window.location.href = '/auth/signin'; return; }
                    if (!res.ok) throw new Error('HTTP Error: ' + res.status);
                    return res.json();
                })
                .then(data => {
                    if (!data) return;
                    successCallback(data.map(event => ({
                        id: event.id,
                        title: event.title,
                        start: event.start,
                        end: event.end,
                        backgroundColor: event.color || '#3788d8',
                        borderColor: event.color || '#3788d8',
                        extendedProps: {
                            device_id: event.extendedProps.device_id,
                            show_clock: event.extendedProps.show_clock,
                            media_playlist: event.extendedProps.media_playlist
                        }
                    })));
                })
                .catch(err => { console.error('Error fetching events:', err); failureCallback(err); });
            },

            dateClick: function(info) {
                const smartDates = getSmartDates(info.date);
                openEventModal(smartDates.start, smartDates.end, null);
            },

            select: function(info) {
                const smartStart = getSmartDates(info.startStr).start;
                const smartEnd = getSmartDates(info.endStr).start;
                openEventModal(smartStart, smartEnd, null);
                calendar.unselect();
            },

            eventClick: function(info) { openEventModal(null, null, info.event); },
            eventDrop: function(info) { updateEventDates(info.event); },
            eventResize: function(info) { updateEventDates(info.event); },
            eventOverlap: function(stillEvent, movingEvent) { return false; }
        });
        calendar.render();
    }

    function openEventModal(startStr, endStr, event) {
        if (!eventModal) return;

        hideEventError();

        const modalTitle = document.getElementById('eventModalLabel');
        const deleteBtn = document.getElementById('deleteEventBtn');
        const showClockCheckbox = document.getElementById('eventShowClock');

        if (event) {
            modalTitle.textContent = 'Edit Event';
            document.getElementById('eventTitle').value = event.title;
            document.getElementById('eventStart')._flatpickr.setDate(event.start);
            document.getElementById('eventEnd')._flatpickr.setDate(event.end);
            document.getElementById('eventColor').value = event.backgroundColor || '#3788d8';

            if (showClockCheckbox) {
                showClockCheckbox.checked = event.extendedProps.show_clock || false;
            }

            currentPlaylist = JSON.parse(JSON.stringify(event.extendedProps.media_playlist || []));

            if (textOnlySwitch) {
                textOnlySwitch.checked = currentPlaylist.length === 0;
                textOnlySwitch.dispatchEvent(new Event('change'));
            }

            if (deleteBtn) deleteBtn.style.display = 'inline-block';
            currentEventId = event.id;
        } else {
            modalTitle.textContent = 'New Event';
            document.getElementById('eventForm').reset();

            if (!startStr || !endStr) {
                const smart = getSmartDates();
                startStr = smart.start;
                endStr = smart.end;
            }

            document.getElementById('eventStart')._flatpickr.setDate(startStr);
            document.getElementById('eventEnd')._flatpickr.setDate(endStr);
            document.getElementById('eventColor').value = '#3788d8';

            if (showClockCheckbox) showClockCheckbox.checked = false;
            if (textOnlySwitch) {
                textOnlySwitch.checked = false;
                textOnlySwitch.dispatchEvent(new Event('change'));
            }

            currentPlaylist = [];
            if (deleteBtn) deleteBtn.style.display = 'none';
            currentEventId = null;
        }

        renderPlaylist();
        eventModal.show();
    }

    function renderPlaylist() {
        const container = document.getElementById('playlistContainer');
        const emptyMsg = document.getElementById('emptyPlaylistMsg');
        if (!container) return;

        if (currentPlaylist.length === 0) {
            container.querySelectorAll('.playlist-item').forEach(item => item.remove());
            if (emptyMsg) {
                emptyMsg.style.display = 'block';
            } else {
                container.innerHTML = `<p class="text-muted text-center my-4" id="emptyPlaylistMsg"><i class="bi bi-info-circle d-block fs-3 mb-2"></i> Click "Select media" to create a playlist</p>`;
            }
            return;
        }

        if (emptyMsg) emptyMsg.style.display = 'none';
        container.querySelectorAll('.playlist-item').forEach(item => item.remove());

        currentPlaylist.forEach((item, index) => {
            const div = document.createElement('div');
            div.className = 'playlist-item';
            div.draggable = true;
            div.dataset.index = index;

            let preview = item.media_type === 'image'
                ? `<img src="/static/uploads/${item.filename}" class="playlist-item-preview" alt="${item.filename}">`
                : `<video class="playlist-item-preview"><source src="/static/uploads/${item.filename}" type="video/mp4"></video>`;

            let durationField = item.media_type === 'image'
                ? `<div class="playlist-item-duration"><label class="form-label small">Time (s):</label><input type="number" class="form-control form-control-sm" value="${item.duration || 10}" min="1" max="300" onchange="updatePlaylistItemDuration(${index}, this.value)"></div>`
                : '<div class="playlist-item-duration"><span class="badge bg-info">Until end</span></div>';

            div.innerHTML = `
                <i class="bi bi-grip-vertical" style="cursor: grab;"></i>
                ${preview}
                <div class="playlist-item-info"><strong>${index + 1}. ${item.filename}</strong><br><small class="text-muted">${item.media_type}</small></div>
                ${durationField}
                <button type="button" class="btn btn-danger btn-sm" onclick="removeFromPlaylist(${index})"><i class="bi bi-trash"></i></button>
            `;

            div.addEventListener('dragstart', handleDragStart);
            div.addEventListener('dragover', handleDragOver);
            div.addEventListener('drop', handleDrop);
            div.addEventListener('dragend', handleDragEnd);

            container.appendChild(div);
        });
    }

    let draggedItem = null;
    function handleDragStart(e) { draggedItem = this; this.classList.add('dragging'); e.dataTransfer.effectAllowed = 'move'; }
    function handleDragOver(e) { if (e.preventDefault) e.preventDefault(); e.dataTransfer.dropEffect = 'move'; const target = e.target.closest('.playlist-item'); if (target && target !== draggedItem) { const rect = target.getBoundingClientRect(); const next = (e.clientY - rect.top) / (rect.bottom - rect.top) > 0.5; target.parentNode.insertBefore(draggedItem, next ? target.nextSibling : target); } return false; }
    function handleDrop(e) { if (e.stopPropagation) e.stopPropagation(); return false; }
    function handleDragEnd(e) { this.classList.remove('dragging'); const items = document.querySelectorAll('.playlist-item'); const newPlaylist = []; items.forEach((item, newIndex) => { const oldIndex = parseInt(item.dataset.index); newPlaylist.push({...currentPlaylist[oldIndex], order: newIndex}); }); currentPlaylist = newPlaylist; renderPlaylist(); }

    window.updatePlaylistItemDuration = function(index, duration) { currentPlaylist[index].duration = parseInt(duration); };
    window.removeFromPlaylist = function(index) { currentPlaylist.splice(index, 1); renderPlaylist(); };

    const addMediaBtn = document.getElementById('addMediaToPlaylist');
    if (addMediaBtn && playlistMediaPickerModal) {
        addMediaBtn.addEventListener('click', function(e) { e.preventDefault(); e.stopPropagation(); playlistMediaPickerModal.show(); });
    }

    document.querySelectorAll('.playlist-media-item').forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault(); e.stopPropagation();
            const mediaId = parseInt(this.dataset.mediaId);
            const exists = currentPlaylist.some(m => m.media_id === mediaId);
            if (exists) return showEventError('This media is already in the playlist!');
            currentPlaylist.push({ media_id: mediaId, filename: this.dataset.mediaFilename, media_type: this.dataset.mediaType, order: currentPlaylist.length, duration: 10 });
            if (playlistMediaPickerModal) playlistMediaPickerModal.hide();
        });
    });

    const saveEventBtn = document.getElementById('saveEventBtn');
    if (saveEventBtn && typeof window.currentDeviceId !== 'undefined' && window.currentDeviceId !== null) {
        saveEventBtn.addEventListener('click', function(e) {
            e.preventDefault(); e.stopPropagation();
            hideEventError();

            const title = document.getElementById('eventTitle').value.trim();
            const start = document.getElementById('eventStart').value;
            const end = document.getElementById('eventEnd').value;
            const color = document.getElementById('eventColor').value;
            const showClock = document.getElementById('eventShowClock') ? document.getElementById('eventShowClock').checked : false;
            const isTextOnly = textOnlySwitch ? textOnlySwitch.checked : false;

            if (!title || !start || !end) return showEventError('Please fill in all required fields (Name, Start, End).');
            if (title.length > 50) return showEventError('Event Name is too long (maximum is 50 characters).');
            if (!isTextOnly && currentPlaylist.length === 0) return showEventError('Please select media or enable "Text Only" mode.');
            if (new Date(start) >= new Date(end)) return showEventError('Event End must be later than Event Start.');

            const payloadPlaylist = isTextOnly ? [] : currentPlaylist;

            const eventData = {
                title: title,
                start_time: convertToLocalISO(start),
                end_time: convertToLocalISO(end),
                device_id: currentDeviceId,
                color: color,
                show_clock: showClock,
                media_playlist: payloadPlaylist
            };

            const url = currentEventId ? `/api/v1/events/${currentEventId}` : '/api/v1/events/';
            const method = currentEventId ? 'PUT' : 'POST';

            fetch(url, { method: method, credentials: 'same-origin', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(eventData) })
            .then(res => {
                if (res.status === 401) { window.location.href = '/auth/signin'; return; }
                if (!res.ok) return res.json().then(err => { throw new Error(err.message || err.error || 'Server processing error.'); });
                return res.json();
            })
            .then(data => {
                if (!data) return;
                if (calendar) calendar.refetchEvents();
                if (eventModal) eventModal.hide();
                currentEventId = null;
                currentPlaylist = [];
                document.getElementById('eventForm').reset();
            })
            .catch(error => showEventError(error.message));
        });
    }

    const deleteEventBtn = document.getElementById('deleteEventBtn');
    if (deleteEventBtn && typeof window.currentDeviceId !== 'undefined' && window.currentDeviceId !== null) {
        deleteEventBtn.addEventListener('click', function(e) {
            e.preventDefault(); e.stopPropagation();
            hideEventError();

            if (!currentEventId) return;
            if (confirm('Are you sure you want to delete this event?')) {
                fetch(`/api/v1/events/${currentEventId}`, { method: 'DELETE', credentials: 'same-origin' })
                .then(res => {
                    if (res.status === 401) { window.location.href = '/auth/signin'; return; }
                    if (!res.ok) return res.json().then(err => { throw new Error(err.message || 'Error deleting event.'); });
                    return res.json();
                })
                .then(data => {
                    if (!data) return;
                    if (calendar) calendar.refetchEvents();
                    if (eventModal) eventModal.hide();
                    currentEventId = null;
                    currentPlaylist = [];
                    document.getElementById('eventForm').reset();
                })
                .catch(error => showEventError(error.message));
            }
        });
    }

    function updateEventDates(event) {
        fetch(`/api/v1/events/${event.id}`, {
            method: 'PUT',
            credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title: event.title,
                start_time: event.start.toISOString(),
                end_time: event.end.toISOString(),
                device_id: currentDeviceId,
                color: event.backgroundColor || '#3788d8',
                show_clock: event.extendedProps.show_clock,
                media_playlist: event.extendedProps.media_playlist
            })
        })
        .then(res => {
            if (res.status === 401) { window.location.href = '/auth/signin'; return; }
            if (!res.ok) return res.json().then(err => { throw new Error(err.message || err.error || 'Overlap detected'); });
            return res.json();
        })
        .catch(error => {
            if (calendar) calendar.refetchEvents();
            showEventError(error.message);
        });
    }

    const defaultMediaPreview = document.getElementById('defaultMediaPreview');
    const defaultMediaSelect = document.getElementById('defaultMediaSelect');
    if (window.currentDeviceMediaId) updateDefaultMediaPreview(window.currentDeviceMediaId);

    if (defaultMediaPreview && window.isAdmin === true) {
        defaultMediaPreview.style.cursor = 'pointer';
        defaultMediaPreview.addEventListener('click', function() { if (mediaPickerModal) mediaPickerModal.show(); });
    } else if (defaultMediaPreview) {
        defaultMediaPreview.style.cursor = 'default';
    }

    document.querySelectorAll('.media-picker-item').forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const mediaId = parseInt(this.dataset.mediaId);
            if (defaultMediaSelect) defaultMediaSelect.value = mediaId;
            document.querySelectorAll('.media-picker-item').forEach(i => i.classList.remove('border-primary', 'border-2'));
            this.classList.add('border-primary', 'border-2');
            updateDefaultMediaPreview(mediaId);
            if (mediaPickerModal) mediaPickerModal.hide();
        });
    });

    const tagCheckboxes = document.querySelectorAll('.tag-filter-checkbox');
    const mediaFilterItems = document.querySelectorAll('.media-filter-item');
    if (tagCheckboxes.length > 0 && mediaFilterItems.length > 0) {
        const allCheckbox = document.getElementById('tag-all');
        tagCheckboxes.forEach(cb => {
            cb.addEventListener('change', function() {
                const isAll = this.dataset.filter === 'all';
                if (isAll && this.checked) { tagCheckboxes.forEach(otherCb => { if (otherCb !== this) otherCb.checked = false; }); }
                else if (!isAll && this.checked) { if (allCheckbox) allCheckbox.checked = false; }
                else if (!isAll && !this.checked) {
                    const anyChecked = Array.from(tagCheckboxes).some(c => c.dataset.filter !== 'all' && c.checked);
                    if (!anyChecked && allCheckbox) allCheckbox.checked = true;
                }
                if (isAll && !this.checked) { const anyChecked = Array.from(tagCheckboxes).some(c => c.dataset.filter !== 'all' && c.checked); if (!anyChecked) this.checked = true; }
                const activeFilters = Array.from(tagCheckboxes).filter(c => c.checked).map(c => c.dataset.filter);
                mediaFilterItems.forEach(item => { const itemTagId = item.dataset.tagId ? item.dataset.tagId.toString() : ""; item.style.display = (activeFilters.includes('all') || activeFilters.includes(itemTagId)) ? '' : 'none'; });
            });
        });
    }

    document.querySelectorAll('.color-preset').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const color = this.dataset.color;
            const eventColorInput = document.getElementById('eventColor');
            if (eventColorInput) eventColorInput.value = color;
            document.querySelectorAll('.color-preset').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
        });
    });

    function updateDefaultMediaPreview(mediaId) {
        if (!window.mediaList) return;
        const media = window.mediaList.find(m => m.id === mediaId);
        if (!media) return;
        let preview = '';
        if (media.media_type === 'image') {
            preview = `<img src="/static/uploads/${media.filename}" class="img-fluid rounded" style="max-height: 200px; object-fit: contain;"><p class="mt-2 mb-0"><strong>${media.filename}</strong></p>`;
        } else {
            preview = `<video class="img-fluid rounded" style="max-height: 200px; object-fit: contain;" autoplay loop muted playsinline><source src="/static/uploads/${media.filename}" type="video/mp4"></video><p class="mt-2 mb-0"><i class="bi bi-play-fill"></i> <strong>${media.filename}</strong></p>`;
        }
        if (defaultMediaPreview) defaultMediaPreview.innerHTML = preview;
    }

    function formatDateTimeLocal(dateStr) {
        const date = new Date(dateStr);
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        return `${year}-${month}-${day}T${hours}:${minutes}`;
    }

    function convertToLocalISO(dateTimeLocalStr) {
        if (!dateTimeLocalStr) return null;
        if (dateTimeLocalStr.length === 16) dateTimeLocalStr += ':00';
        return dateTimeLocalStr;
    }
});
