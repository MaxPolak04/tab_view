const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))

const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]')
const popoverList = [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl))


const nav = document.querySelector('.navbar-collapse')

document.addEventListener('click', () => {
    if (nav.classList.contains('show')) {
        nav.classList.remove('show')
    }
})


document.addEventListener("DOMContentLoaded", function () {
    const errorMessages = [
        "Doctor, heal thyself. The admin panel needs a hug.",
        "Well, this escalated quickly. Error 500 has entered the chat.",
        "The server tripped over its own code. Please stand by.",
        "Even the backend needs a coffee break sometimes ☕.",
        "Error 500: The system is currently questioning its life choices.",
        "Oops! Something broke. You're the admin, so... good luck!",
        "The server is down. Probably watching cat videos again.",
        "500 Internal Server Error. Have you tried turning it off and on again?",
        "This is fine 🔥. Everything is fine.",
        "Congratulations! You've unlocked the rare and majestic Error 500."
    ]

    function getRandomErrorMessage() {
        const index = Math.floor(Math.random() * errorMessages.length);
        return errorMessages[index];
    }


    function showError500() {
        const message = getRandomErrorMessage();
        console.error(message);
        document.getElementById("error-text").innerText = message;
    }

    showError500()
})


document.querySelector('form').addEventListener('submit', function(e) {
    const btn = this.querySelector('button[type="submit"]');
    btn.disabled = true;
    btn.innerText = 'Uploading...';
  });


setTimeout(() => {
    document.querySelectorAll('.flash-overlay .alert').forEach(alert => {
        alert.classList.add('fade-out');
        setTimeout(() => alert.remove(), 500);
    });
}, 3000);



// Calendar with media playlist

document.addEventListener('DOMContentLoaded', function() {
    // === INITIALIZATION ===
    const calendarEl = document.getElementById('calendar');
    if (!calendarEl) {
        console.log('No calendar on this page');
        return;
    }
    
    const currentDeviceId = window.currentDeviceId;
    let calendar;
    let currentEventId = null;
    let eventModal;
    let mediaPickerModal;
    let playlistMediaPickerModal;
    let currentPlaylist = [];
    
    // Bootstrap Modals Initialization
    const eventModalEl = document.getElementById('eventModal');
    const mediaPickerModalEl = document.getElementById('mediaPickerModal');
    const playlistMediaPickerModalEl = document.getElementById('playlistMediaPickerModal');
    
    eventModal = new bootstrap.Modal(eventModalEl);
    mediaPickerModal = new bootstrap.Modal(mediaPickerModalEl);
    playlistMediaPickerModal = new bootstrap.Modal(playlistMediaPickerModalEl);
    
    // Event listener for closing the playlist modal
    playlistMediaPickerModalEl.addEventListener('hidden.bs.modal', function() {
        console.log('Modal playlist closed - rendering playlist');
        renderPlaylist();
    });
    
    // === CALENDAR ===
    calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'timeGridWeek',
        locale: 'pl',
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
            // FullCalendar automatically passes info.startStr and info.endStr
            const params = new URLSearchParams({
                device_id: currentDeviceId,
                start: info.startStr,
                end: info.endStr
            });

            fetch(`/api/v1/events/?device_id=${currentDeviceId}`)
                .then(response => response.json())
                .then(data => {
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
    
    // === EVENT MODAL FUNCTIONS ===
    
    function openEventModal(startStr, endStr, event) {
        const modalTitle = document.getElementById('eventModalLabel');
        const deleteBtn = document.getElementById('deleteEventBtn');
        
        if (event) {
            // Edit mode
            modalTitle.textContent = 'Edit schedule';
            document.getElementById('eventTitle').value = event.title;
            document.getElementById('eventStart').value = formatDateTimeLocal(event.start);
            document.getElementById('eventEnd').value = formatDateTimeLocal(event.end);
            document.getElementById('eventColor').value = event.color || '#3788d8';
            
            // DEEP COPY of playlist (to avoid references)
            currentPlaylist = JSON.parse(JSON.stringify(event.extendedProps.media_playlist || []));
            
            deleteBtn.style.display = 'inline-block';
            currentEventId = event.id;
        } else {
            // Creation mode
            modalTitle.textContent = 'Add schedule';
            document.getElementById('eventForm').reset();
            document.getElementById('eventStart').value = startStr ? formatDateTimeLocal(startStr) : '';
            document.getElementById('eventEnd').value = endStr ? formatDateTimeLocal(endStr) : '';
            document.getElementById('eventColor').value = '#3788d8';
            
            // IMPORTANT: Clear playlist when creating a new event
            currentPlaylist = [];
            
            deleteBtn.style.display = 'none';
            currentEventId = null;
        }
        
        console.log('OpenEventModal - currentPlaylist:', currentPlaylist);
        
        // Render playlist
        renderPlaylist();
        
        // Show modal
        eventModal.show();
    }
    
    function renderPlaylist() {
        const container = document.getElementById('playlistContainer');
        const emptyMsg = document.getElementById('emptyPlaylistMsg');
        
        console.log('=== RENDER PLAYLIST ===');
        console.log('Playlist to render:', currentPlaylist);
        console.log('Container:', container);
        console.log('EmptyMsg:', emptyMsg);
        
        if (!container) {
            console.error('Missing playlistContainer element');
            return;
        }
        
        if (currentPlaylist.length === 0) {
            console.log('Playlist is empty – showing message');
            // Remove only playlist-item, NOT emptyMsg
            const items = container.querySelectorAll('.playlist-item');
            items.forEach(item => item.remove());
            
            // Show message (may be null if it was removed)
            if (emptyMsg) {
                emptyMsg.style.display = 'block';
            } else {
                // Restore message if it was removed
                container.innerHTML = `
                    <p class="text-muted text-center" id="emptyPlaylistMsg">
                        <i class="bi bi-info-circle"></i> Click "Add media" to create a playlist
                    </p>
                `;
            }
            return;
        }
        
        console.log(`Rendering ${currentPlaylist.length} items`);
        
        // Hide message
        if (emptyMsg) {
            emptyMsg.style.display = 'none';
        }
        
        // Remove only playlist-item, NOT emptyMsg
        const items = container.querySelectorAll('.playlist-item');
        items.forEach(item => item.remove());
        
        currentPlaylist.forEach((item, index) => {
            const div = document.createElement('div');
            div.className = 'playlist-item';
            div.draggable = true;
            div.dataset.index = index;
            
            // Preview
            let preview = '';
            if (item.media_type === 'image') {
                preview = `<img src="/static/uploads/${item.filename}" class="playlist-item-preview" alt="${item.filename}">`;
            } else {
                preview = `<video class="playlist-item-preview">
                    <source src="/static/uploads/${item.filename}" type="video/mp4">
                </video>`;
            }
            
            // Duration field only for images
            let durationField = '';
            if (item.media_type === 'image') {
                durationField = `
                    <div class="playlist-item-duration">
                        <label class="form-label small">Czas (s):</label>
                        <input type="number" class="form-control form-control-sm" 
                               value="${item.duration || 10}" 
                               min="1" max="300"
                               onchange="updatePlaylistItemDuration(${index}, this.value)">
                    </div>
                `;
            } else {
                durationField = '<div class="playlist-item-duration"><span class="badge bg-info">Until end of video</span></div>';
            }
            
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
            
            // Drag & drop handlers
            div.addEventListener('dragstart', handleDragStart);
            div.addEventListener('dragover', handleDragOver);
            div.addEventListener('drop', handleDrop);
            div.addEventListener('dragend', handleDragEnd);
            
            container.appendChild(div);
        });
        
        console.log('Rendering complete. Items in DOM:', container.children.length);
    }
    
    // === DRAG & DROP ===
    let draggedItem = null;
    
    function handleDragStart(e) {
        draggedItem = this;
        this.classList.add('dragging');
        e.dataTransfer.effectAllowed = 'move';
    }
    
    function handleDragOver(e) {
        if (e.preventDefault) {
            e.preventDefault();
        }
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
        if (e.stopPropagation) {
            e.stopPropagation();
        }
        return false;
    }
    
    function handleDragEnd(e) {
        this.classList.remove('dragging');
        
        // Read the new order
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
    
    document.getElementById('addMediaToPlaylist').addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        console.log('Opening media selection modal');
        playlistMediaPickerModal.show();
    });
    
    // Selecting media from the grid
    document.querySelectorAll('.playlist-media-item').forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const mediaId = parseInt(this.dataset.mediaId);
            const filename = this.dataset.mediaFilename;
            const mediaType = this.dataset.mediaType;
            
            console.log('Selected media:', { mediaId, filename, mediaType });
            
            // Check if media is already in the playlist
            const exists = currentPlaylist.some(m => m.media_id === mediaId);
            if (exists) {
                alert('This media is already in the playlist!');
                return;
            }
            
            // Add to playlisty
            currentPlaylist.push({
                media_id: mediaId,
                filename: filename,
                media_type: mediaType,
                order: currentPlaylist.length,
                duration: 10
            });
            
            console.log('Playlist after adding:', currentPlaylist);
            
            // Close modal (the 'hidden.bs.modal' event listener will render the playlist)
            playlistMediaPickerModal.hide();
        });
    });
    
    // === SAVING EVENT ===
    
    document.getElementById('saveEventBtn').addEventListener('click', function(e) {
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
        
        console.log('Sending event:', eventData);
        
        const url = currentEventId ? `/api/v1/events/${currentEventId}` : '/api/v1/events/';
        const method = currentEventId ? 'PUT' : 'POST';
        
        fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(eventData)
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(err.error || 'HTTP Error: ' + response.status);
                });
            }
            return response.json();
        })
        .then(data => {
            console.log('Event saved:', data);
            
            // Refresh calendar
            calendar.refetchEvents();
            
            // Close modal
            eventModal.hide();
            
            // Clear state
            currentEventId = null;
            currentPlaylist = [];
            document.getElementById('eventForm').reset();
            
            alert(method === 'PUT' ? 'Schedule updated!' : 'Schedule created!');
        })
        .catch(error => {
            console.error('Error saving event:', error);
            alert('Error: ' + error.message);
        });
    });
    
    // === DELETING EVENT ===
    
    document.getElementById('deleteEventBtn').addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        if (!currentEventId) return;
        
        if (confirm('Are you sure you want to delete this schedule?')) {
            fetch(`/api/v1/events/${currentEventId}`, {
                method: 'DELETE'
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('HTTP Error: ' + response.status);
                }
                return response.json();
            })
            .then(data => {
                console.log('Event deleted:', data);
                
                // Refresh calendar
                calendar.refetchEvents();
                
                // Close modal
                eventModal.hide();
                
                // Clear state
                currentEventId = null;
                currentPlaylist = [];
                document.getElementById('eventForm').reset();
                
                alert('Schedule deleted!');
            })
            .catch(error => {
                console.error('Error deleting event:', error);
                alert('Error while deleting schedule');
            });
        }
    });
    
    // === DATE UPDATE AFTER DRAG ===
    
    function updateEventDates(event) {
        fetch(`/api/v1/events/${event.id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                title: event.title,
                start_time: event.start.toISOString(),
                end_time: event.end.toISOString(),
                device_id: currentDeviceId,
                color: event.color || '#3788d8',
                media_playlist: event.extendedProps.media_playlist
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('HTTP Error: ' + response.status);
            }
            return response.json();
        })
        .catch(error => {
            console.error('Event update error:', error);
            calendar.refetchEvents();
            alert('Error when moving the schedule');
        });
    }
    
    // === DEFAULT MEDIA CHOICE ===
    
    const defaultMediaPreview = document.getElementById('defaultMediaPreview');
    const defaultMediaSelect = document.getElementById('defaultMediaSelect');
    
    // Show currently selected media
    if (window.currentDeviceMediaId) {
        updateDefaultMediaPreview(window.currentDeviceMediaId);
    }
    
    defaultMediaPreview.addEventListener('click', function() {
        mediaPickerModal.show();
    });
    
    document.querySelectorAll('.media-picker-item').forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const mediaId = parseInt(this.dataset.mediaId);
            defaultMediaSelect.value = mediaId;
            updateDefaultMediaPreview(mediaId);
            mediaPickerModal.hide();
        });
    });
    
    // === COLOR PRESETS ===
    
    document.querySelectorAll('.color-preset').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const color = this.dataset.color;
            document.getElementById('eventColor').value = color;
            
            // Highlight the selected preset
            document.querySelectorAll('.color-preset').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
        });
    });
    
    function updateDefaultMediaPreview(mediaId) {
        const media = window.mediaList.find(m => m.id === mediaId);
        if (!media) return;
        
        let preview = '';
        if (media.media_type === 'image') {
            preview = `
                <img src="/static/uploads/${media.filename}" 
                     class="img-fluid rounded" 
                     style="max-height: 200px;">
                <p class="mt-2 mb-0"><strong>${media.filename}</strong></p>
            `;
        } else {
            preview = `
                <video class="img-fluid rounded" style="max-height: 200px;">
                    <source src="/static/uploads/${media.filename}" type="video/mp4">
                </video>
                <p class="mt-2 mb-0">
                    <i class="bi bi-play-fill"></i> <strong>${media.filename}</strong>
                </p>
            `;
        }
        defaultMediaPreview.innerHTML = preview;
    }
    
    // === SUPPORTING FUNCTIONS ===
    
    function formatDateTimeLocal(dateStr) {
        // Convert to Date object
        const date = new Date(dateStr);
        
        // IMPORTANT: Download local time (not UTC)
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        
        return `${year}-${month}-${day}T${hours}:${minutes}`;
    }
    
    function convertToLocalISO(dateTimeLocalStr) {
        // Wprowadź: „2025-11-05T14:30” (format datetime-local)
        // Output: “2025-11-05T14:30:00” (ISO format without conversion to UTC)
        
        if (!dateTimeLocalStr) return null;
        
        // Add seconds if missing
        if (dateTimeLocalStr.length === 16) {
            dateTimeLocalStr += ':00';
        }
        
        return dateTimeLocalStr;
    }
});
