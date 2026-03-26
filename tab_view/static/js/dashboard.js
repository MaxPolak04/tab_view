document.addEventListener('DOMContentLoaded', function() {
    let calendar;
    let currentEventId = null;
    let currentGroupId = null;
    let currentPlaylist = [];
    let fetchAvailabilityTimeout = null;

    const eventModalEl = document.getElementById('dashboardEventModal');
    const eventModal = eventModalEl ? new bootstrap.Modal(eventModalEl) : null;

    const playlistMediaPickerModalEl = document.getElementById('playlistMediaPickerModal');
    const playlistMediaPickerModal = playlistMediaPickerModalEl ? new bootstrap.Modal(playlistMediaPickerModalEl) : null;

    if (playlistMediaPickerModalEl) {
        playlistMediaPickerModalEl.addEventListener('hidden.bs.modal', function() { renderPlaylist(); });
    }

    // Check availability logic
    const startInput = document.getElementById('eventStart');
    const endInput = document.getElementById('eventEnd');

    function checkAvailability() {
        const start = startInput.value;
        const end = endInput.value;

        if (!start || !end) return;

        // Reset visual state
        document.querySelectorAll('.device-checkbox').forEach(cb => {
            cb.disabled = false;
        });
        document.querySelectorAll('.device-checkbox-wrapper').forEach(wrapper => {
            wrapper.classList.remove('bg-light', 'opacity-50');
        });
        document.querySelectorAll('.device-busy-text').forEach(text => {
            text.style.setProperty('display', 'none', 'important');
            text.textContent = '';
        });

        // Add exclude_group_id if we are editing
        let url = `/api/v1/events/availability?start=${convertToLocalISO(start)}&end=${convertToLocalISO(end)}`;
        if (currentGroupId) {
            url += `&exclude_group_id=${currentGroupId}`;
        }

        fetch(url, { credentials: 'same-origin' })
            .then(res => res.json())
            .then(data => {
                // data = { "1": {"busy": true, "event_title": "Promo"} }
                for (const [deviceId, info] of Object.entries(data)) {
                    const cb = document.getElementById(`device-${deviceId}`);
                    const wrapper = document.getElementById(`device-wrapper-${deviceId}`);
                    const text = document.getElementById(`busy-text-${deviceId}`);

                    if (cb && info.busy) {
                        cb.disabled = true;
                        cb.checked = false;
                        wrapper.classList.add('bg-light', 'opacity-50');
                        text.textContent = `(Zajęte przez: ${info.event_title})`;
                        text.style.setProperty('display', 'block', 'important');
                    }
                }
            })
            .catch(err => console.error("Error checking availability:", err));
    }

    [startInput, endInput].forEach(input => {
        input.addEventListener('change', () => {
            clearTimeout(fetchAvailabilityTimeout);
            fetchAvailabilityTimeout = setTimeout(checkAvailability, 300);
        });
    });

    // Calendar
    const calendarEl = document.getElementById('dashboardCalendar');
    if (calendarEl) {
        calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'dayGridMonth',
            locale: 'en',
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

            // Group events visually by group_id in memory
            eventDataTransform: function(eventData) {
                // Append device name to title for visual distinction
                let devName = eventData.extendedProps?.device_name || "Unknown";
                eventData.title = `${eventData.title} (${devName})`;
                return eventData;
            },

            events: function(info, successCallback, failureCallback) {
                const params = new URLSearchParams({
                    start: info.startStr,
                    end: info.endStr
                });

                fetch(`/api/v1/events/?${params.toString()}`, { credentials: 'same-origin' })
                    .then(res => {
                        if (res.status === 401) window.location.href = '/auth/signin';
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
                                group_id: event.group_id,
                                device_id: event.extendedProps.device_id,
                                device_name: event.extendedProps.device_name,
                                media_playlist: event.extendedProps.media_playlist
                            }
                        })));
                    })
                    .catch(err => failureCallback(err));
            },
            select: function(info) {
                openEventModal(info.startStr, info.endStr, null);
                calendar.unselect();
            },
            eventClick: function(info) {
                // When clicking a single device's event, load the whole GROUP data
                openEventModal(null, null, info.event);
            },
            eventDrop: function(info) { updateEventDates(info.event); },
            eventResize: function(info) { updateEventDates(info.event); },
        });
        calendar.render();
    }

    function openEventModal(startStr, endStr, event) {
        if (!eventModal) return;

        const deleteBtn = document.getElementById('deleteEventBtn');
        document.querySelectorAll('.device-checkbox').forEach(cb => { cb.checked = false; cb.disabled = false; });
        document.querySelectorAll('.device-busy-text').forEach(t => t.style.setProperty('display', 'none', 'important'));
        document.querySelectorAll('.device-checkbox-wrapper').forEach(w => w.classList.remove('bg-light', 'opacity-50'));

        if (event) {
            // Edit Mode
            // Remove the appended device name "(Device Name)" to get raw title
            let rawTitle = event.title.replace(/\s\([^)]+\)$/, '');
            document.getElementById('eventTitle').value = rawTitle;
            document.getElementById('eventStart').value = formatDateTimeLocal(event.start);
            document.getElementById('eventEnd').value = formatDateTimeLocal(event.end);
            document.getElementById('eventColor').value = event.backgroundColor || '#3788d8';

            currentPlaylist = JSON.parse(JSON.stringify(event.extendedProps.media_playlist || []));
            currentEventId = event.id;
            currentGroupId = event.extendedProps.group_id;

            // Check the boxes for ALL devices sharing this group_id currently loaded in the calendar
            const allCalendarEvents = calendar.getEvents();
            const groupEvents = allCalendarEvents.filter(e => e.extendedProps.group_id === currentGroupId);

            groupEvents.forEach(e => {
                const cb = document.getElementById(`device-${e.extendedProps.device_id}`);
                if (cb) cb.checked = true;
            });

            if (deleteBtn) deleteBtn.style.display = 'inline-block';
        } else {
            // Create Mode
            document.getElementById('eventForm').reset();
            document.getElementById('eventStart').value = startStr ? formatDateTimeLocal(startStr) : '';
            document.getElementById('eventEnd').value = endStr ? formatDateTimeLocal(endStr) : '';
            document.getElementById('eventColor').value = '#3788d8';

            currentPlaylist = [];
            currentEventId = null;
            currentGroupId = null;
            if (deleteBtn) deleteBtn.style.display = 'none';
        }

        checkAvailability(); // Initial check
        renderPlaylist();
        eventModal.show();
    }

    // Tag Filtering logic specifically for dashboard
    const tagCheckboxes = document.querySelectorAll('.tag-filter-checkbox');
    const mediaFilterItems = document.querySelectorAll('.media-filter-item');

    if (tagCheckboxes.length > 0 && mediaFilterItems.length > 0) {
        const allCheckbox = document.getElementById('tag-all');

        tagCheckboxes.forEach(cb => {
            cb.addEventListener('change', function() {
                const isAll = this.dataset.filter === 'all';
                if (isAll && this.checked) {
                    tagCheckboxes.forEach(otherCb => { if (otherCb !== this) otherCb.checked = false; });
                } else if (!isAll && this.checked) {
                    if (allCheckbox) allCheckbox.checked = false;
                } else if (!isAll && !this.checked) {
                    const anyChecked = Array.from(tagCheckboxes).some(c => c.dataset.filter !== 'all' && c.checked);
                    if (!anyChecked && allCheckbox) allCheckbox.checked = true;
                }
                if (isAll && !this.checked) {
                     const anyChecked = Array.from(tagCheckboxes).some(c => c.dataset.filter !== 'all' && c.checked);
                     if (!anyChecked) this.checked = true;
                }

                const activeFilters = Array.from(tagCheckboxes).filter(c => c.checked).map(c => c.dataset.filter);
                mediaFilterItems.forEach(item => {
                    const itemTagId = item.dataset.tagId ? item.dataset.tagId.toString() : "";
                    item.style.display = (activeFilters.includes('all') || activeFilters.includes(itemTagId)) ? '' : 'none';
                });
            });
        });
    }

    // Standard playlist render logic (similar to scripts.js)
    function renderPlaylist() {
        const container = document.getElementById('playlistContainer');
        const emptyMsg = document.getElementById('emptyPlaylistMsg');
        if (!container) return;

        const items = container.querySelectorAll('.playlist-item');
        items.forEach(item => item.remove());

        if (currentPlaylist.length === 0) {
            if (emptyMsg) emptyMsg.style.display = 'block';
            return;
        }

        if (emptyMsg) emptyMsg.style.display = 'none';

        currentPlaylist.forEach((item, index) => {
            const div = document.createElement('div');
            div.className = 'playlist-item';
            div.draggable = true;
            div.dataset.index = index;

            let preview = item.media_type === 'image'
                ? `<img src="/static/uploads/${item.filename}" class="playlist-item-preview">`
                : `<video class="playlist-item-preview"><source src="/static/uploads/${item.filename}" type="video/mp4"></video>`;

            let durationField = item.media_type === 'image'
                ? `<div class="playlist-item-duration"><label class="form-label small">Time (s):</label><input type="number" class="form-control form-control-sm" value="${item.duration || 10}" onchange="updatePlaylistItemDuration(${index}, this.value)"></div>`
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
    function handleDragOver(e) { e.preventDefault(); e.dataTransfer.dropEffect = 'move'; const target = e.target.closest('.playlist-item'); if (target && target !== draggedItem) { const next = (e.clientY - target.getBoundingClientRect().top) / (target.getBoundingClientRect().bottom - target.getBoundingClientRect().top) > 0.5; target.parentNode.insertBefore(draggedItem, next ? target.nextSibling : target); } return false; }
    function handleDrop(e) { e.stopPropagation(); return false; }
    function handleDragEnd(e) { this.classList.remove('dragging'); const items = document.querySelectorAll('.playlist-item'); const newPlaylist = []; items.forEach((item, newIndex) => { newPlaylist.push({...currentPlaylist[parseInt(item.dataset.index)], order: newIndex}); }); currentPlaylist = newPlaylist; renderPlaylist(); }

    window.updatePlaylistItemDuration = function(index, duration) { currentPlaylist[index].duration = parseInt(duration); };
    window.removeFromPlaylist = function(index) { currentPlaylist.splice(index, 1); renderPlaylist(); };

    document.getElementById('addMediaToPlaylist')?.addEventListener('click', e => { e.preventDefault(); playlistMediaPickerModal?.show(); });
    document.querySelectorAll('.playlist-media-item').forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const mediaId = parseInt(this.dataset.mediaId);
            if (currentPlaylist.some(m => m.media_id === mediaId)) return alert('Already in playlist!');
            currentPlaylist.push({ media_id: mediaId, filename: this.dataset.mediaFilename, media_type: this.dataset.mediaType, order: currentPlaylist.length, duration: 10 });
            playlistMediaPickerModal?.hide();
        });
    });

    document.getElementById('saveEventBtn')?.addEventListener('click', e => {
        e.preventDefault();

        const selectedDevices = Array.from(document.querySelectorAll('.device-checkbox:checked')).map(cb => parseInt(cb.value));
        if (selectedDevices.length === 0) return alert('Select at least one device!');

        const title = document.getElementById('eventTitle').value.trim();
        const start = document.getElementById('eventStart').value;
        const end = document.getElementById('eventEnd').value;

        if (!title || !start || !end) return alert('Fill in all fields!');
        if (currentPlaylist.length === 0) return alert('Add media!');
        if (new Date(start) >= new Date(end)) return alert('End date must be later!');

        const payload = {
            title: title,
            start_time: convertToLocalISO(start),
            end_time: convertToLocalISO(end),
            color: document.getElementById('eventColor').value,
            device_ids: selectedDevices,
            media_playlist: currentPlaylist
        };

        const url = currentEventId ? `/api/v1/events/${currentEventId}` : '/api/v1/events/';
        const method = currentEventId ? 'PUT' : 'POST';

        fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
            credentials: 'same-origin'
        })
        .then(res => {
            if (!res.ok) return res.json().then(err => { throw new Error(err.message || 'Error'); });
            return res.json();
        })
        .then(() => {
            calendar.refetchEvents();
            eventModal.hide();
        })
        .catch(err => alert(err.message));
    });

    document.getElementById('deleteEventBtn')?.addEventListener('click', e => {
        e.preventDefault();
        if (!currentEventId || !confirm('Delete schedule from ALL associated devices?')) return;

        fetch(`/api/v1/events/${currentEventId}`, { method: 'DELETE', credentials: 'same-origin' })
            .then(res => res.ok ? res.json() : Promise.reject('Error deleting'))
            .then(() => { calendar.refetchEvents(); eventModal.hide(); })
            .catch(err => alert(err));
    });

    function updateEventDates(event) {
        // Find all devices sharing this group currently
        const allCalendarEvents = calendar.getEvents();
        const groupDeviceIds = allCalendarEvents.filter(e => e.extendedProps.group_id === event.extendedProps.group_id).map(e => e.extendedProps.device_id);

        let rawTitle = event.title.replace(/\s\([^)]+\)$/, '');

        fetch(`/api/v1/events/${event.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title: rawTitle,
                start_time: event.start.toISOString(),
                end_time: event.end.toISOString(),
                device_ids: groupDeviceIds,
                color: event.backgroundColor || '#3788d8',
                media_playlist: event.extendedProps.media_playlist
            }),
            credentials: 'same-origin'
        })
        .then(res => {
            if (!res.ok) return res.json().then(err => { throw new Error(err.message || 'Overlap detected'); });
            return res.json();
        })
        .catch(err => {
            calendar.refetchEvents();
            alert(err.message);
        });
    }

    // Color presets
    document.querySelectorAll('.color-preset').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            document.getElementById('eventColor').value = this.dataset.color;
        });
    });

    function formatDateTimeLocal(dStr) {
        const d = new Date(dStr);
        return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}T${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`;
    }
    function convertToLocalISO(dStr) { return dStr ? (dStr.length === 16 ? dStr + ':00' : dStr) : null; }
});
