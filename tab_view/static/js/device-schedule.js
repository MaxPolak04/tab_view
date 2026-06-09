document.addEventListener('DOMContentLoaded', function() {
    const currentDeviceId = window.currentDeviceId;
    let calendar;
    let currentEventId = null;
    let currentPlaylist = [];
    let isGroupEvent = false;

    // GLOBAL FIX FOR BOOTSTRAP 5 NESTED MODALS
    // Zabezpiecza tło i scroll dla modala bazowego, gdy zamykane są modale podrzędne
    document.addEventListener('hidden.bs.modal', function () {
        if (document.querySelectorAll('.modal.show').length > 0) {
            document.body.classList.add('modal-open');
        }
    });

    const eventModalEl = document.getElementById('eventModal');
    const eventModal = eventModalEl ? new bootstrap.Modal(eventModalEl) : null;

    const deleteOptionsModalEl = document.getElementById('deleteOptionsModal');
    const deleteOptionsModal = deleteOptionsModalEl ? new bootstrap.Modal(deleteOptionsModalEl) : null;

    const playlistMediaPickerModalEl = document.getElementById('playlistMediaPickerModal');
    const playlistMediaPickerModal = playlistMediaPickerModalEl ? new bootstrap.Modal(playlistMediaPickerModalEl) : null;

    if (playlistMediaPickerModalEl) {
        playlistMediaPickerModalEl.addEventListener('hidden.bs.modal', function() {
            renderPlaylist();
        });
    }

    // --- AJAX UPLOAD LOGIC ---
    const uploadAjaxModalEl = document.getElementById('uploadAjaxModal');
    const uploadAjaxModal = uploadAjaxModalEl ? new bootstrap.Modal(uploadAjaxModalEl) : null;
    const ajaxUploadForm = document.getElementById('ajaxUploadForm');
    const btnSubmitAjaxUpload = document.getElementById('btnSubmitAjaxUpload');

    // EXPLICIT MODAL CHAINING TO PREVENT BACKDROP CORRUPTION
    const btnOpenUploadAjax = document.getElementById('btnOpenUploadAjax');
    if (btnOpenUploadAjax) {
        btnOpenUploadAjax.addEventListener('click', function(e) {
            e.preventDefault();
            playlistMediaPickerModal?.hide();
            // Czekamy na zakonczenie animacji zamykania poprzedniego modala
            setTimeout(() => { uploadAjaxModal?.show(); }, 400);
        });
    }

    const btnBackToLibrary = document.getElementById('btnBackToLibrary');
    if (btnBackToLibrary) {
        btnBackToLibrary.addEventListener('click', function(e) {
            e.preventDefault();
            uploadAjaxModal?.hide();
            setTimeout(() => { playlistMediaPickerModal?.show(); }, 400);
        });
    }

    if (uploadAjaxModalEl) {
        uploadAjaxModalEl.addEventListener('hidden.bs.modal', function() {
            if (ajaxUploadForm) ajaxUploadForm.reset();
            document.getElementById('ajaxUploadError').classList.add('d-none');
        });
    }

    if (btnSubmitAjaxUpload && ajaxUploadForm) {
        btnSubmitAjaxUpload.addEventListener('click', function(e) {
            e.preventDefault();

            const formData = new FormData(ajaxUploadForm);

            const originalText = btnSubmitAjaxUpload.innerHTML;
            btnSubmitAjaxUpload.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Uploading...';
            btnSubmitAjaxUpload.disabled = true;
            document.getElementById('ajaxUploadError').classList.add('d-none');

            fetch('/media/api/upload', {
                method: 'POST',
                body: formData,
                credentials: 'same-origin'
            })
            .then(res => res.json().then(data => ({ status: res.status, body: data })))
            .then(result => {
                if (result.status === 200 && result.body.success) {
                    result.body.media.forEach(m => {
                        addMediaToGrid(m);
                    });

                    uploadAjaxModal.hide();
                    // Zmiana na bezpieczne asynchroniczne otwarcie
                    setTimeout(() => { playlistMediaPickerModal?.show(); }, 400);
                } else {
                    const errEl = document.getElementById('ajaxUploadError');
                    errEl.textContent = result.body.message || 'Upload failed. Check your inputs.';
                    errEl.classList.remove('d-none');
                }
            })
            .catch(err => {
                const errEl = document.getElementById('ajaxUploadError');
                errEl.textContent = 'Network error during upload.';
                errEl.classList.remove('d-none');
            })
            .finally(() => {
                btnSubmitAjaxUpload.innerHTML = originalText;
                btnSubmitAjaxUpload.disabled = false;
            });
        });
    }

    function addMediaToGrid(media) {
        const container = document.getElementById('mediaGridContainer');
        if (!container) return;

        const col = document.createElement('div');
        col.className = 'col-6 col-md-4 col-lg-3 media-filter-item';
        col.dataset.tagId = media.tag_id;

        let preview = media.media_type === 'image'
            ? `<img src="/static/uploads/${media.filename}" class="card-img-top object-fit-cover" style="height: 150px;" loading="lazy">`
            : `<video class="card-img-top object-fit-cover" style="height: 150px;" preload="metadata"><source src="/static/uploads/${media.filename}" type="video/mp4"></video>`;

        let badge = media.media_type === 'video'
            ? `<span class="badge bg-primary mb-1"><i class="bi bi-play-fill"></i> Video</span>`
            : `<span class="badge bg-success mb-1"><i class="bi bi-image"></i> Image</span>`;

        col.innerHTML = `
            <div class="card playlist-media-item h-100 shadow-sm border-secondary-subtle"
                 data-media-id="${media.id}"
                 data-media-filename="${media.filename}"
                 data-media-type="${media.media_type}"
                 style="cursor: pointer;">
                ${preview}
                <div class="card-body p-2">
                    ${badge}
                    <small class="d-block text-truncate fw-medium" title="${media.filename}">${media.filename}</small>
                </div>
            </div>
        `;

        const card = col.querySelector('.playlist-media-item');
        card.addEventListener('click', function(e) {
            e.preventDefault(); e.stopPropagation();
            const mediaId = parseInt(this.dataset.mediaId);
            const exists = currentPlaylist.some(m => m.media_id === mediaId);
            if (exists) {
                if (typeof showEventError === 'function') showEventError('This media is already in the playlist!');
                return;
            }
            currentPlaylist.push({ media_id: mediaId, filename: this.dataset.mediaFilename, media_type: this.dataset.mediaType, order: currentPlaylist.length, duration: 10 });
            playlistMediaPickerModal?.hide();
        });

        container.insertBefore(col, container.firstChild);

        if (typeof window.mediaList !== 'undefined') window.mediaList.push(media);
        if (typeof updateMediaFilters === 'function') updateMediaFilters();
    }
    // --- END AJAX UPLOAD LOGIC ---

    // Logic for "All Day" toggle
    document.getElementById('eventAllDay')?.addEventListener('change', function(e) {
        if (e.target.checked) {
            const startInput = document.getElementById('eventStart');
            const endInput = document.getElementById('eventEnd');

            if (startInput && startInput._flatpickr && startInput._flatpickr.selectedDates.length > 0) {
                let dStart = new Date(startInput._flatpickr.selectedDates[0]);
                dStart.setHours(0, 0, 0, 0);
                startInput._flatpickr.setDate(dStart, true);

                let dEnd = new Date(dStart);
                dEnd.setDate(dEnd.getDate() + 1);

                if (endInput && endInput._flatpickr) {
                    endInput._flatpickr.setDate(dEnd, true);
                }
            }
        }
    });

    function showEventError(message) {
        const errorContainer = document.getElementById('eventFormError');
        const errorText = document.getElementById('eventFormErrorText');
        if (errorContainer && errorText) {
            errorText.textContent = message;
            errorContainer.classList.remove('d-none');
            document.querySelector('#eventModal .modal-body').scrollTop = 0;
        } else {
            alert(message);
        }
    }

    function hideEventError() {
        const errorContainer = document.getElementById('eventFormError');
        if (errorContainer) {
            errorContainer.classList.add('d-none');
        }
    }

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
        },
        onChange: function(selectedDates, dateStr, instance) {
            const allDaySwitch = document.getElementById('eventAllDay');
            if (allDaySwitch && allDaySwitch.checked && selectedDates.length > 0) {
                const d = selectedDates[0];
                if (d.getHours() !== 0 || d.getMinutes() !== 0) {
                    allDaySwitch.checked = false;
                }
            }
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
            dayMaxEvents: true,
            editable: true,
            selectable: true,
            selectMirror: true,
            selectOverlap: true,

            events: function(info, successCallback, failureCallback) {
                const params = new URLSearchParams({ start: info.startStr, end: info.endStr });
                fetch(`/api/v1/events/?${params.toString()}`, { credentials: 'same-origin' })
                .then(res => {
                    if (res.status === 401) { window.location.href = '/auth/signin'; return; }
                    if (!res.ok) throw new Error('HTTP Error: ' + res.status);
                    return res.json();
                })
                .then(data => {
                    if (!data) return;

                    const groupedEvents = {};
                    data.forEach(event => {
                        const gId = event.group_id || `single-${event.id}`;

                        if (!groupedEvents[gId]) {
                            groupedEvents[gId] = {
                                id: event.id,
                                title: event.title,
                                start: event.start,
                                end: event.end,
                                backgroundColor: event.color || '#3788d8',
                                borderColor: event.color || '#3788d8',
                                extendedProps: {
                                    group_id: event.group_id,
                                    device_ids: [],
                                    show_clock: event.extendedProps.show_clock,
                                    show_weather: event.extendedProps.show_weather,
                                    media_playlist: event.extendedProps.media_playlist
                                }
                            };
                        }

                        if (event.extendedProps.device_id === currentDeviceId) {
                            groupedEvents[gId].id = event.id;
                        }

                        if (!groupedEvents[gId].extendedProps.device_ids.includes(event.extendedProps.device_id)) {
                            groupedEvents[gId].extendedProps.device_ids.push(event.extendedProps.device_id);
                        }
                    });

                    const filteredEvents = Object.values(groupedEvents).filter(event =>
                        event.extendedProps.device_ids.includes(currentDeviceId)
                    );

                    successCallback(filteredEvents);
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

        if (document.getElementById('eventAllDay')) {
            document.getElementById('eventAllDay').checked = false;
        }

        const modalTitle = document.getElementById('eventModalLabel');
        const deleteBtn = document.getElementById('deleteEventBtn');
        const showClockCheckbox = document.getElementById('eventShowClock');
        const showWeatherCheckbox = document.getElementById('eventShowWeather');

        if (event) {
            modalTitle.textContent = 'Edit Event';
            document.getElementById('eventTitle').value = event.title;
            document.getElementById('eventStart')._flatpickr.setDate(event.start);
            document.getElementById('eventEnd')._flatpickr.setDate(event.end);
            document.getElementById('eventColor').value = event.backgroundColor || '#3788d8';

            if (showClockCheckbox) {
                showClockCheckbox.checked = event.extendedProps.show_clock === true;
            }
            if (showWeatherCheckbox) {
                showWeatherCheckbox.checked = event.extendedProps.show_weather === true;
            }

            currentPlaylist = JSON.parse(JSON.stringify(event.extendedProps.media_playlist || []));
            currentEventId = event.id;

            isGroupEvent = event.extendedProps.device_ids && event.extendedProps.device_ids.length > 1;

            if (textOnlySwitch) {
                textOnlySwitch.checked = currentPlaylist.length === 0;
                textOnlySwitch.dispatchEvent(new Event('change'));
            }

            if (deleteBtn) deleteBtn.style.display = 'inline-block';
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
            if (showWeatherCheckbox) showWeatherCheckbox.checked = false;

            if (textOnlySwitch) {
                textOnlySwitch.checked = false;
                textOnlySwitch.dispatchEvent(new Event('change'));
            }

            currentPlaylist = [];
            currentEventId = null;
            isGroupEvent = false;
            if (deleteBtn) deleteBtn.style.display = 'none';
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
            const showWeather = document.getElementById('eventShowWeather') ? document.getElementById('eventShowWeather').checked : false;
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
                show_weather: showWeather,
                media_playlist: payloadPlaylist
            };

            const url = currentEventId ? `/api/v1/events/${currentEventId}?scope=instance` : '/api/v1/events/';
            const method = currentEventId ? 'PUT' : 'POST';

            fetch(url, { method: method, credentials: 'same-origin', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(eventData) })
            .then(res => {
                if (res.status === 401) { window.location.href = '/auth/signin'; return; }
                if (res.status === 409) return res.json().then(err => { throw new Error(err.message || err.error || 'Overlap detected'); });
                if (!res.ok) return res.json().then(err => { throw new Error(err.message || err.error || 'HTTP Error: ' + res.status); });
                return res.json();
            })
            .then(data => {
                if (!data) return;
                if (calendar) calendar.refetchEvents();
                if (eventModal) eventModal.hide();
                currentEventId = null;
                currentPlaylist = [];
                isGroupEvent = false;
                document.getElementById('eventForm').reset();
            })
            .catch(error => showEventError(error.message));
        });
    }

    const executeDeletion = (scope) => {
        if (!currentEventId) return;

        fetch(`/api/v1/events/${currentEventId}?scope=${scope}`, { method: 'DELETE', credentials: 'same-origin' })
        .then(res => {
            if (res.status === 401) { window.location.href = '/auth/signin'; return; }
            if (!res.ok) throw new Error('Error deleting event.');
            return res.json();
        })
        .then(data => {
            if (!data) return;
            if (calendar) calendar.refetchEvents();
            if (eventModal) eventModal.hide();
            if (deleteOptionsModal) deleteOptionsModal.hide();
            currentEventId = null;
            currentPlaylist = [];
            isGroupEvent = false;
            document.getElementById('eventForm').reset();
        })
        .catch(error => showEventError(error.message));
    };

    const deleteEventBtn = document.getElementById('deleteEventBtn');
    if (deleteEventBtn && typeof window.currentDeviceId !== 'undefined' && window.currentDeviceId !== null) {
        deleteEventBtn.addEventListener('click', function(e) {
            e.preventDefault(); e.stopPropagation();
            hideEventError();

            if (!currentEventId) return;

            if (isGroupEvent && deleteOptionsModal) {
                eventModal.hide();
                // Opoznienie dla zapobiegniecia utraty tla
                setTimeout(() => { deleteOptionsModal.show(); }, 400);
            } else {
                if (confirm('Are you sure you want to delete this event from THIS specific device?')) {
                    executeDeletion('instance');
                }
            }
        });
    }

    document.getElementById('deleteInstanceBtn')?.addEventListener('click', function(e) {
        e.preventDefault();
        executeDeletion('instance');
    });

    document.getElementById('deleteGroupBtn')?.addEventListener('click', function(e) {
        e.preventDefault();
        executeDeletion('group');
    });

    deleteOptionsModalEl?.addEventListener('hidden.bs.modal', function(e) {
        // Jesli event nie zostal usuniety, chcemy wrocic do modala z eventem
        if (currentEventId && eventModal) {
             setTimeout(() => { eventModal.show(); }, 400);
        }
    });

    function updateEventDates(event) {
        fetch(`/api/v1/events/${event.id}?scope=instance`, {
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
                show_weather: event.extendedProps.show_weather,
                media_playlist: event.extendedProps.media_playlist
            })
        })
        .then(res => {
            if (res.status === 401) { window.location.href = '/auth/signin'; return; }
            if (res.status === 409) return res.json().then(err => { throw new Error(err.message || err.error || 'Overlap detected'); });
            if (!res.ok) throw new Error('HTTP Error: ' + res.status);
            return res.json();
        })
        .catch(error => {
            if (calendar) calendar.refetchEvents();
            showEventError(error.message || 'Error when moving the event');
        });
    }

    const tagCheckboxes = document.querySelectorAll('.tag-filter-checkbox');
    const mediaFilterItems = document.querySelectorAll('.media-filter-item');
    const allCheckbox = document.getElementById('tag-all');

    function updateMediaFilters() {
        if (!tagCheckboxes.length || !mediaFilterItems.length) return;
        const checkedTags = Array.from(tagCheckboxes).filter(c => c.checked).map(c => c.dataset.filter);

        mediaFilterItems.forEach(item => {
            const tagId = item.dataset.tagId ? item.dataset.tagId.toString() : "";
            if (checkedTags.includes('all') || checkedTags.includes(tagId)) {
                item.style.display = '';
            } else {
                item.style.display = 'none';
            }
        });
    }

    if (tagCheckboxes.length > 0) {
        tagCheckboxes.forEach(cb => {
            cb.addEventListener('change', function() {
                if (this.dataset.filter === 'all') {
                    if (this.checked) {
                        tagCheckboxes.forEach(c => { if (c !== this) c.checked = false; });
                    } else {
                        const anyOtherChecked = Array.from(tagCheckboxes).some(c => c.dataset.filter !== 'all' && c.checked);
                        if (!anyOtherChecked) this.checked = true;
                    }
                } else {
                    if (this.checked) {
                        if (allCheckbox) allCheckbox.checked = false;
                    } else {
                        const anyOtherChecked = Array.from(tagCheckboxes).some(c => c.dataset.filter !== 'all' && c.checked);
                        if (!anyOtherChecked && allCheckbox) allCheckbox.checked = true;
                    }
                }
                updateMediaFilters();
            });
        });
        setTimeout(updateMediaFilters, 50);
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

    function formatDateTimeLocal(dStr) {
        const d = new Date(dStr);
        return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}T${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`;
    }

    function convertToLocalISO(dStr) { return dStr ? (dStr.length === 16 ? dStr + ':00' : dStr) : null; }
});
