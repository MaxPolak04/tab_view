// Calendar with media playlist
document.addEventListener('DOMContentLoaded', function() {
    // === INITIALIZATION ===
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

    // === CALENDAR ===
    const calendarEl = document.getElementById('calendar');
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
            selectMirror: true,

            events: function(info, successCallback, failureCallback) {
                const params = new URLSearchParams({
                    device_id: currentDeviceId,
                    start: info.startStr,
                    end: info.endStr
                });

                fetch(`/api/v1/events/?device_id=${currentDeviceId}`, {
                    credentials: 'same-origin'
                })
                .then(response => {
                    if (response.status === 401) {
                        window.location.href = '/auth/signin';
                        return;
                    }
                    if (!response.ok) {
                        throw new Error('HTTP Error: ' + response.status);
                    }
                    return response.json();
                })
                .then(data => {
                    if (!data) return;

                    const events = data.map(event => ({
                        id: event.id,
                        title: event.title,
                        start: event.start,
                        end: event.end,
                        backgroundColor: event.color || '#3788d8',
                        borderColor: event.color || '#3788d8',
                        extendedProps: {
                            device_id: event.extendedProps.device_id,
                            media_playlist: event.extendedProps.media_playlist
                        }
                    }));
                    successCallback(events);
                })
                .catch(error => {
                    console.error('Error fetching events:', error);
                    failureCallback(error);
                });
            },

            select: function(info) {
                openEventModal(info.startStr, info.endStr, null);
                calendar.unselect();
            },

            eventClick: function(info) {
                openEventModal(null, null, info.event);
            },

            eventDrop: function(info) {
                updateEventDates(info.event);
            },

            eventResize: function(info) {
                updateEventDates(info.event);
            },

            selectOverlap: function(event) {
                return false;
            },

            eventOverlap: function(stillEvent, movingEvent) {
                return false;
            }
        });

        calendar.render();
    }

    // === EVENT MODAL FUNCTIONS ===
    function openEventModal(startStr, endStr, event) {
        if (!eventModal) return;

        const modalTitle = document.getElementById('eventModalLabel');
        const deleteBtn = document.getElementById('deleteEventBtn');

        if (event) {
            modalTitle.textContent = 'Edit schedule';
            document.getElementById('eventTitle').value = event.title;
            document.getElementById('eventStart').value = formatDateTimeLocal(event.start);
            document.getElementById('eventEnd').value = formatDateTimeLocal(event.end);
            document.getElementById('eventColor').value = event.backgroundColor || '#3788d8';

            currentPlaylist = JSON.parse(JSON.stringify(event.extendedProps.media_playlist || []));

            if (deleteBtn) deleteBtn.style.display = 'inline-block';
            currentEventId = event.id;
        } else {
            modalTitle.textContent = 'Add schedule';
            document.getElementById('eventForm').reset();
            document.getElementById('eventStart').value = startStr ? formatDateTimeLocal(startStr) : '';
            document.getElementById('eventEnd').value = endStr ? formatDateTimeLocal(endStr) : '';
            document.getElementById('eventColor').value = '#3788d8';

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
            const items = container.querySelectorAll('.playlist-item');
            items.forEach(item => item.remove());

            if (emptyMsg) {
                emptyMsg.style.display = 'block';
            } else {
                container.innerHTML = `
                    <p class="text-muted text-center" id="emptyPlaylistMsg">
                        <i class="bi bi-info-circle"></i> Click "Add media" to create a playlist
                    </p>
                `;
            }
            return;
        }

        if (emptyMsg) emptyMsg.style.display = 'none';

        const items = container.querySelectorAll('.playlist-item');
        items.forEach(item => item.remove());

        currentPlaylist.forEach((item, index) => {
            const div = document.createElement('div');
            div.className = 'playlist-item';
            div.draggable = true;
            div.dataset.index = index;

            let preview = item.media_type === 'image'
                ? `<img src="/static/uploads/${item.filename}" class="playlist-item-preview" alt="${item.filename}">`
                : `<video class="playlist-item-preview"><source src="/static/uploads/${item.filename}" type="video/mp4"></video>`;

            let durationField = item.media_type === 'image'
                ? `
                    <div class="playlist-item-duration">
                        <label class="form-label small">Time (s):</label>
                        <input type="number" class="form-control form-control-sm"
                               value="${item.duration || 10}"
                               min="1" max="300"
                               onchange="updatePlaylistItemDuration(${index}, this.value)">
                    </div>
                `
                : '<div class="playlist-item-duration"><span class="badge bg-info">Until end of video</span></div>';

            div.innerHTML = `
                <i class="bi bi-grip-vertical" style="cursor: grab;"></i>
                ${preview}
                <div class="playlist-item-info">
                    <strong>${index + 1}. ${item.filename}</strong>
                    <br><small class="text-muted">${item.media_type}</small>
                </div>
                ${durationField}
                <button type="button" class="btn btn-danger btn-sm" onclick="removeFromPlaylist(${index})">
                    <i class="bi bi-trash"></i>
                </button>
            `;

            div.addEventListener('dragstart', handleDragStart);
            div.addEventListener('dragover', handleDragOver);
            div.addEventListener('drop', handleDrop);
            div.addEventListener('dragend', handleDragEnd);

            container.appendChild(div);
        });
    }

    // === DRAG & DROP ===
    let draggedItem = null;

    function handleDragStart(e) {
        draggedItem = this;
        this.classList.add('dragging');
        e.dataTransfer.effectAllowed = 'move';
    }

    function handleDragOver(e) {
        if (e.preventDefault) e.preventDefault();
        e.dataTransfer.dropEffect = 'move';

        const target = e.target.closest('.playlist-item');
        if (target && target !== draggedItem) {
            const rect = target.getBoundingClientRect();
            const next = (e.clientY - rect.top) / (rect.bottom - rect.top) > 0.5;
            target.parentNode.insertBefore(draggedItem, next ? target.nextSibling : target);
        }
        return false;
    }

    function handleDrop(e) {
        if (e.stopPropagation) e.stopPropagation();
        return false;
    }

    function handleDragEnd(e) {
        this.classList.remove('dragging');

        const items = document.querySelectorAll('.playlist-item');
        const newPlaylist = [];
        items.forEach((item, newIndex) => {
            const oldIndex = parseInt(item.dataset.index);
            newPlaylist.push({...currentPlaylist[oldIndex], order: newIndex});
        });
        currentPlaylist = newPlaylist;
        renderPlaylist();
    }

    // === PLAYLIST HELPER FUNCTIONS ===
    window.updatePlaylistItemDuration = function(index, duration) {
        currentPlaylist[index].duration = parseInt(duration);
    };

    window.removeFromPlaylist = function(index) {
        currentPlaylist.splice(index, 1);
        renderPlaylist();
    };

    // === ADDING MEDIA TO PLAYLIST ===
    const addMediaBtn = document.getElementById('addMediaToPlaylist');
    if (addMediaBtn && playlistMediaPickerModal) {
        addMediaBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            playlistMediaPickerModal.show();
        });
    }

    document.querySelectorAll('.playlist-media-item').forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();

            const mediaId = parseInt(this.dataset.mediaId);
            const filename = this.dataset.mediaFilename;
            const mediaType = this.dataset.mediaType;

            const exists = currentPlaylist.some(m => m.media_id === mediaId);
            if (exists) {
                alert('This media is already in the playlist!');
                return;
            }

            currentPlaylist.push({
                media_id: mediaId,
                filename: filename,
                media_type: mediaType,
                order: currentPlaylist.length,
                duration: 10
            });

            if (playlistMediaPickerModal) playlistMediaPickerModal.hide();
        });
    });

    // === SAVING EVENT ===
    const saveEventBtn = document.getElementById('saveEventBtn');
    if (saveEventBtn && typeof window.currentDeviceId !== 'undefined' && window.currentDeviceId !== null) {
        saveEventBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();

            const title = document.getElementById('eventTitle').value.trim();
            const start = document.getElementById('eventStart').value;
            const end = document.getElementById('eventEnd').value;
            const color = document.getElementById('eventColor').value;

            if (!title || !start || !end) {
                alert('Fill in all fields!');
                return;
            }

            if (currentPlaylist.length === 0) {
                alert('Add at least one media item to the playlist!');
                return;
            }

            if (new Date(start) >= new Date(end)) {
                alert('End date must be later than start date!');
                return;
            }

            const eventData = {
                title: title,
                start_time: convertToLocalISO(start),
                end_time: convertToLocalISO(end),
                device_id: currentDeviceId,
                color: color,
                media_playlist: currentPlaylist
            };

            const url = currentEventId ? `/api/v1/events/${currentEventId}` : '/api/v1/events/';
            const method = currentEventId ? 'PUT' : 'POST';

            fetch(url, {
                method: method,
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(eventData)
            })
            .then(response => {
                if (response.status === 401) {
                    alert('Session expired. Please log in again.');
                    window.location.href = '/auth/signin';
                    return;
                }
                if (response.status === 409) {
                    return response.json().then(err => {
                        throw new Error(err.message || err.error || 'This schedule overlaps with an existing one.');
                    });
                }
                if (response.status === 415) {
                    return response.json().then(err => {
                        throw new Error('Invalid Content-Type. Please contact the administrator.');
                    });
                }
                if (!response.ok) {
                    return response.json().then(err => {
                        throw new Error(err.message || err.error || 'HTTP Error: ' + response.status);
                    });
                }
                return response.json();
            })
            .then(data => {
                if (!data) return;
                if (calendar) calendar.refetchEvents();
                if (eventModal) eventModal.hide();

                currentEventId = null;
                currentPlaylist = [];
                document.getElementById('eventForm').reset();

                alert(method === 'PUT' ? 'Schedule updated successfully!' : 'Schedule created successfully!');
            })
            .catch(error => {
                console.error('Error saving event:', error);
                alert('Error: ' + error.message);
            });
        });
    }

    // === DELETING EVENT ===
    const deleteEventBtn = document.getElementById('deleteEventBtn');
    if (deleteEventBtn && typeof window.currentDeviceId !== 'undefined' && window.currentDeviceId !== null) {
        deleteEventBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();

            if (!currentEventId) return;

            if (confirm('Are you sure you want to delete this schedule?')) {
                fetch(`/api/v1/events/${currentEventId}`, {
                    method: 'DELETE',
                    credentials: 'same-origin'
                })
                .then(response => {
                    if (response.status === 401) {
                        alert('Session expired. Please log in again.');
                        window.location.href = '/auth/signin';
                        return;
                    }
                    if (!response.ok) {
                        throw new Error('HTTP Error: ' + response.status);
                    }
                    return response.json();
                })
                .then(data => {
                    if (!data) return;
                    if (calendar) calendar.refetchEvents();
                    if (eventModal) eventModal.hide();

                    currentEventId = null;
                    currentPlaylist = [];
                    document.getElementById('eventForm').reset();

                    alert('Schedule deleted successfully!');
                })
                .catch(error => {
                    console.error('Error deleting event:', error);
                    alert('Error while deleting schedule');
                });
            }
        });
    }

    // === DATE UPDATE AFTER DRAG ===
    function updateEventDates(event) {
        fetch(`/api/v1/events/${event.id}`, {
            method: 'PUT',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                title: event.title,
                start_time: event.start.toISOString(),
                end_time: event.end.toISOString(),
                device_id: currentDeviceId,
                color: event.backgroundColor || '#3788d8',
                media_playlist: event.extendedProps.media_playlist
            })
        })
        .then(response => {
            if (response.status === 401) {
                alert('Session expired. Please log in again.');
                window.location.href = '/auth/signin';
                return;
            }
            if (response.status === 409) {
                return response.json().then(err => {
                    throw new Error(err.message || err.error || 'This schedule overlaps with an existing one.');
                });
            }
            if (!response.ok) {
                throw new Error('HTTP Error: ' + response.status);
            }
            return response.json();
        })
        .catch(error => {
            console.error('Event update error:', error);
            if (calendar) calendar.refetchEvents();
            alert(error.message || 'Error when moving the schedule');
        });
    }

    // === DEFAULT MEDIA CHOICE ===
    const defaultMediaPreview = document.getElementById('defaultMediaPreview');
    const defaultMediaSelect = document.getElementById('defaultMediaSelect');

    if (window.currentDeviceMediaId) {
        updateDefaultMediaPreview(window.currentDeviceMediaId);
    }

    if (defaultMediaPreview && window.isAdmin === true) {
        defaultMediaPreview.style.cursor = 'pointer';
        defaultMediaPreview.addEventListener('click', function() {
            if (mediaPickerModal) mediaPickerModal.show();
        });
    } else if (defaultMediaPreview) {
        defaultMediaPreview.style.cursor = 'default';
    }

    document.querySelectorAll('.media-picker-item').forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const mediaId = parseInt(this.dataset.mediaId);
            if (defaultMediaSelect) {
                defaultMediaSelect.value = mediaId;
            }

            // Remove border from previously selected
            document.querySelectorAll('.media-picker-item').forEach(i => i.classList.remove('border-primary', 'border-2'));
            // Add border to selected
            this.classList.add('border-primary', 'border-2');

            updateDefaultMediaPreview(mediaId);
            if (mediaPickerModal) mediaPickerModal.hide();
        });
    });

    // === TAG FILTERING ===
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

    // === COLOR PRESETS ===
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
            preview = `
                <img src="/static/uploads/${media.filename}"
                     class="img-fluid rounded"
                     style="max-height: 200px; object-fit: contain;">
                <p class="mt-2 mb-0"><strong>${media.filename}</strong></p>
            `;
        } else {
            preview = `
                <video class="img-fluid rounded" style="max-height: 200px; object-fit: contain;" autoplay loop muted playsinline>
                    <source src="/static/uploads/${media.filename}" type="video/mp4">
                </video>
                <p class="mt-2 mb-0">
                    <i class="bi bi-play-fill"></i> <strong>${media.filename}</strong>
                </p>
            `;
        }
        if (defaultMediaPreview) {
            defaultMediaPreview.innerHTML = preview;
        }
    }

    // === HELPER FUNCTIONS ===
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
        if (dateTimeLocalStr.length === 16) {
            dateTimeLocalStr += ':00';
        }
        return dateTimeLocalStr;
    }
});
