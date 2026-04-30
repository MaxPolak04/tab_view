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

    function getRandomHexColor() {
        return '#' + Math.floor(Math.random() * 16777215).toString(16).padStart(6, '0');
    }

    function showEventError(message) {
        const errorContainer = document.getElementById('eventFormError');
        const errorText = document.getElementById('eventFormErrorText');
        if (errorContainer && errorText) {
            errorText.textContent = message;
            errorContainer.classList.remove('d-none');
            document.querySelector('#dashboardEventModal .modal-body').scrollTop = 0;
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
        altFormat: "Y-m-d H:i",
        time_24hr: true,
        locale: "pl",
        allowInput: true,
        clickOpens: false,
        altInputClass: "form-control form-control-lg shadow-sm rounded-start-3",
        onReady: function(selectedDates, dateStr, instance) {
            const btnContainer = document.createElement("div");
            btnContainer.className = "d-grid px-2 pb-2 pt-1";
            const btn = document.createElement("button");
            btn.className = "btn btn-primary btn-sm shadow-sm rounded-pill";
            btn.type = "button";
            btn.innerText = "Apply";
            btn.addEventListener("click", function() { instance.close(); });
            btnContainer.appendChild(btn);
            instance.calendarContainer.appendChild(btnContainer);
        },
        onInput: function() {
            clearTimeout(fetchAvailabilityTimeout);
            fetchAvailabilityTimeout = setTimeout(() => { checkAvailability(); }, 300);
        },
        onChange: function() {
            clearTimeout(fetchAvailabilityTimeout);
            fetchAvailabilityTimeout = setTimeout(() => { checkAvailability(); }, 300);
        },
        onClose: function() {
            checkAvailability();
        }
    };

    const startFp = flatpickr("#eventStart", flatpickrConfig);
    const endFp = flatpickr("#eventEnd", flatpickrConfig);

    document.getElementById('btn-start-calendar')?.addEventListener('click', () => { startFp.open(); });
    document.getElementById('btn-end-calendar')?.addEventListener('click', () => { endFp.open(); });

    const startInput = document.getElementById('eventStart');
    const endInput = document.getElementById('eventEnd');

    function checkAvailability() {
        const start = document.getElementById('eventStart')._flatpickr.input.value;
        const end = document.getElementById('eventEnd')._flatpickr.input.value;
        if (!start || !end) return;

        document.querySelectorAll('.device-checkbox').forEach(cb => { cb.disabled = false; });
        document.querySelectorAll('.device-checkbox-wrapper').forEach(wrapper => { wrapper.classList.remove('bg-light', 'opacity-50'); });
        document.querySelectorAll('.device-busy-text').forEach(text => { text.style.visibility = 'hidden'; text.textContent = ''; });

        let url = `/api/v1/events/availability?start=${convertToLocalISO(start)}&end=${convertToLocalISO(end)}`;
        if (currentGroupId) url += `&exclude_group_id=${currentGroupId}`;

        fetch(url, { credentials: 'same-origin' })
            .then(res => res.json())
            .then(data => {
                for (const [deviceId, info] of Object.entries(data)) {
                    const cb = document.getElementById(`device-${deviceId}`);
                    const wrapper = document.getElementById(`device-wrapper-${deviceId}`);
                    const text = document.getElementById(`busy-text-${deviceId}`);
                    if (cb && info.busy) {
                        cb.disabled = true;
                        cb.checked = false;
                        wrapper.classList.add('bg-light', 'opacity-50');
                        text.textContent = `(Busy: ${info.event_title})`;
                        text.style.visibility = 'visible';
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

    const searchInput = document.getElementById('deviceSearch');
    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            const term = e.target.value.toLowerCase();
            document.querySelectorAll('.device-checkbox-wrapper').forEach(wrapper => {
                const label = wrapper.querySelector('label strong').textContent.toLowerCase();
                if (label.includes(term)) { wrapper.parentElement.style.display = ''; }
                else { wrapper.parentElement.style.display = 'none'; }
            });
        });
    }

    document.querySelectorAll('.device-checkbox-wrapper').forEach(wrapper => {
        wrapper.style.cursor = 'pointer';
        wrapper.addEventListener('click', function(e) {
            if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'LABEL' && !e.target.closest('label')) {
                const cb = this.querySelector('.device-checkbox');
                if (cb && !cb.disabled) {
                    cb.checked = !cb.checked;
                    cb.dispatchEvent(new Event('change'));
                }
            }
        });
    });

    const textOnlySwitch = document.getElementById('eventTextOnly');
    const mediaSection = document.getElementById('mediaSection');

    if (textOnlySwitch && mediaSection) {
        textOnlySwitch.addEventListener('change', function(e) {
            if (e.target.checked) { mediaSection.style.display = 'none'; }
            else { mediaSection.style.display = 'block'; }
        });
    }

    const calendarEl = document.getElementById('dashboardCalendar');
    if (calendarEl) {
        calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'dayGridMonth',
            locale: 'pl',
            eventTimeFormat: { hour: '2-digit', minute: '2-digit', hour12: false },
            slotLabelFormat: { hour: '2-digit', minute: '2-digit', hour12: false },
            headerToolbar: { left: 'prev,next today', center: 'title', right: 'dayGridMonth,timeGridWeek,timeGridDay' },
            slotMinTime: '06:00:00',
            slotMaxTime: '22:00:00',
            allDaySlot: false,
            editable: true,
            selectable: true,

            events: function(info, successCallback, failureCallback) {
                const params = new URLSearchParams({ start: info.startStr, end: info.endStr });
                fetch(`/api/v1/events/?${params.toString()}`, { credentials: 'same-origin' })
                    .then(res => {
                        if (res.status === 401) window.location.href = '/auth/signin';
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
                                        device_names: [],
                                        show_clock: event.extendedProps.show_clock,
                                        media_playlist: event.extendedProps.media_playlist
                                    }
                                };
                            }

                            if (!groupedEvents[gId].extendedProps.device_ids.includes(event.extendedProps.device_id)) {
                                groupedEvents[gId].extendedProps.device_ids.push(event.extendedProps.device_id);
                                groupedEvents[gId].extendedProps.device_names.push(event.extendedProps.device_name);
                            }
                        });

                        const uniqueEvents = Object.values(groupedEvents).map(event => {
                            let devNames = event.extendedProps.device_names.join(', ');
                            event.title = `${event.title} (${devNames})`;
                            return event;
                        });

                        successCallback(uniqueEvents);
                    })
                    .catch(err => failureCallback(err));
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
        });
        calendar.render();
    }

    function openEventModal(startStr, endStr, event) {
        if (!eventModal) return;

        hideEventError();

        const deleteBtn = document.getElementById('deleteEventBtn');
        const showClockCheckbox = document.getElementById('eventShowClock');
        const eventModalLabel = document.getElementById('eventModalLabel');

        document.querySelectorAll('.device-checkbox').forEach(cb => { cb.checked = false; cb.disabled = false; });
        document.querySelectorAll('.device-busy-text').forEach(t => t.style.visibility = 'hidden');
        document.querySelectorAll('.device-checkbox-wrapper').forEach(w => w.classList.remove('bg-light', 'opacity-50'));

        if (event) {
            eventModalLabel.textContent = 'Edit Event';
            let rawTitle = event.title.replace(/\s\([^)]+\)$/, '');
            document.getElementById('eventTitle').value = rawTitle;
            document.getElementById('eventStart')._flatpickr.setDate(event.start);
            document.getElementById('eventEnd')._flatpickr.setDate(event.end);
            document.getElementById('eventColor').value = event.backgroundColor || '#3788d8';

            if (showClockCheckbox) {
                showClockCheckbox.checked = event.extendedProps.show_clock || false;
            }

            currentPlaylist = JSON.parse(JSON.stringify(event.extendedProps.media_playlist || []));
            currentEventId = event.id;
            currentGroupId = event.extendedProps.group_id;

            if (textOnlySwitch) {
                textOnlySwitch.checked = currentPlaylist.length === 0;
                textOnlySwitch.dispatchEvent(new Event('change'));
            }

            const groupDeviceIds = event.extendedProps.device_ids || [];
            groupDeviceIds.forEach(devId => {
                const cb = document.getElementById(`device-${devId}`);
                if (cb) cb.checked = true;
            });

            if (deleteBtn) deleteBtn.style.display = 'inline-block';
        } else {
            eventModalLabel.textContent = 'New Event';
            document.getElementById('eventForm').reset();

            if (!startStr || !endStr) {
                const smart = getSmartDates();
                startStr = smart.start;
                endStr = smart.end;
            }

            document.getElementById('eventStart')._flatpickr.setDate(startStr);
            document.getElementById('eventEnd')._flatpickr.setDate(endStr);
            document.getElementById('eventColor').value = getRandomHexColor();

            if (showClockCheckbox) showClockCheckbox.checked = false;
            if (textOnlySwitch) {
                textOnlySwitch.checked = false;
                textOnlySwitch.dispatchEvent(new Event('change'));
            }

            currentPlaylist = [];
            currentEventId = null;
            currentGroupId = null;
            if (deleteBtn) deleteBtn.style.display = 'none';
        }

        checkAvailability();
        renderPlaylist();
        eventModal.show();
    }

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
            if (currentPlaylist.some(m => m.media_id === mediaId)) return showEventError('Already in playlist!');
            currentPlaylist.push({ media_id: mediaId, filename: this.dataset.mediaFilename, media_type: this.dataset.mediaType, order: currentPlaylist.length, duration: 10 });
            playlistMediaPickerModal?.hide();
        });
    });

    document.getElementById('saveEventBtn')?.addEventListener('click', e => {
        e.preventDefault();
        hideEventError();

        const selectedDevices = Array.from(document.querySelectorAll('.device-checkbox:checked')).map(cb => parseInt(cb.value));
        if (selectedDevices.length === 0) return showEventError('Please select at least one device to display the event.');

        const title = document.getElementById('eventTitle').value.trim();
        const start = document.getElementById('eventStart')._flatpickr.input.value;
        const end = document.getElementById('eventEnd')._flatpickr.input.value;

        const showClockCheckbox = document.getElementById('eventShowClock');
        const showClock = showClockCheckbox ? showClockCheckbox.checked : false;

        const isTextOnly = textOnlySwitch ? textOnlySwitch.checked : false;

        if (!title || !start || !end) return showEventError('Please fill in all required fields (Name, Start, End).');
        if (title.length > 50) return showEventError('Event Name is too long (maximum is 50 characters).');
        if (!isTextOnly && currentPlaylist.length === 0) return showEventError('Please select media or enable "Text Only" mode.');
        if (new Date(start) >= new Date(end)) return showEventError('Event End must be later than Event Start.');

        const payloadPlaylist = isTextOnly ? [] : currentPlaylist;

        const payload = {
            title: title,
            start_time: convertToLocalISO(start),
            end_time: convertToLocalISO(end),
            color: document.getElementById('eventColor').value,
            show_clock: showClock,
            device_ids: selectedDevices,
            media_playlist: payloadPlaylist
        };

        const url = currentEventId ? `/api/v1/events/${currentEventId}?scope=group` : '/api/v1/events/';
        const method = currentEventId ? 'PUT' : 'POST';

        fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
            credentials: 'same-origin'
        })
        .then(res => {
            if (!res.ok) return res.json().then(err => { throw new Error(err.message || err.error || 'Server processing error.'); });
            return res.json();
        })
        .then(() => {
            calendar.refetchEvents();
            eventModal.hide();
        })
        .catch(err => showEventError(err.message));
    });

    document.getElementById('deleteEventBtn')?.addEventListener('click', e => {
        e.preventDefault();
        hideEventError();

        if (!currentEventId || !confirm('Are you sure you want to delete this event from ALL associated devices?')) return;

        fetch(`/api/v1/events/${currentEventId}?scope=group`, { method: 'DELETE', credentials: 'same-origin' })
            .then(res => {
                if (!res.ok) return res.json().then(err => { throw new Error(err.message || 'Error deleting event.'); });
                return res.json();
            })
            .then(() => { calendar.refetchEvents(); eventModal.hide(); })
            .catch(err => showEventError(err.message));
    });

    function updateEventDates(event) {
        const groupDeviceIds = event.extendedProps.device_ids || [];
        let rawTitle = event.title.replace(/\s\([^)]+\)$/, '');

        fetch(`/api/v1/events/${event.id}?scope=group`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title: rawTitle,
                start_time: event.start.toISOString(),
                end_time: event.end.toISOString(),
                device_ids: groupDeviceIds,
                color: event.backgroundColor || '#3788d8',
                show_clock: event.extendedProps.show_clock,
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
            showEventError(err.message);
        });
    }

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
});
