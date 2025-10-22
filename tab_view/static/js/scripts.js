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


document.addEventListener('DOMContentLoaded', function() {
    const calendarEl = document.getElementById('calendar');
    
    // Sprawdź czy element kalendarza istnieje na stronie
    if (!calendarEl) return;
    
    // Pobierz ID aktualnego device z szablonu
    const currentDeviceId = window.currentDeviceId;
    let calendar;
    let currentEventId = null;
    let eventModal;
    
    // Inicjalizacja Bootstrap Modal
    eventModal = new bootstrap.Modal(document.getElementById('eventModal'));
    
    calendar = new FullCalendar.Calendar(calendarEl, {
        // Podstawowe ustawienia
        initialView: 'timeGridWeek',
        locale: 'pl',
        
        // Nagłówek z przyciskami
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        
        // Ustawienia czasu
        slotMinTime: '06:00:00',
        slotMaxTime: '22:00:00',
        allDaySlot: false,
        
        // Włącz interakcje
        editable: true,
        selectable: true,
        selectMirror: true,
        
        // POBIERANIE EVENTÓW Z API - tylko dla tego device
        events: function(info, successCallback, failureCallback) {
            fetch(`/api/v1/events/?device_id=${currentDeviceId}`)
                .then(response => response.json())
                .then(data => {
                    // Filtruj eventy tylko dla tego urządzenia
                    const filteredEvents = data
                        .filter(event => event.extendedProps.device_id === currentDeviceId)
                        .map(event => ({
                            id: event.id,
                            title: event.title,
                            start: event.start,
                            end: event.end,
                            extendedProps: {
                                device_id: event.extendedProps.device_id,
                                media_id: event.extendedProps.media_id
                            }
                        }));
                    successCallback(filteredEvents);
                })
                .catch(error => {
                    console.error('Błąd pobierania eventów:', error);
                    failureCallback(error);
                });
        },
        
        // KLIKNIĘCIE W PUSTY OBSZAR - otwórz modal do tworzenia
        select: function(info) {
            openEventModal(info.startStr, info.endStr, null);
            calendar.unselect();
        },
        
        // KLIKNIĘCIE W EVENT - otwórz modal do edycji
        eventClick: function(info) {
            openEventModal(null, null, info.event);
        },
        
        // PRZECIĄGANIE EVENTU
        eventDrop: function(info) {
            updateEventDates(info.event);
        },
        
        // ZMIANA ROZMIARU EVENTU
        eventResize: function(info) {
            updateEventDates(info.event);
        },
        
        // Sprawdzenie nakładających się eventów
        selectOverlap: function(event) {
            return false; // Nie pozwól na nakładające się eventy
        },
        
        eventOverlap: function(stillEvent, movingEvent) {
            return false; // Nie pozwól na nakładające się eventy
        }
    });
    
    calendar.render();
    
    // === FUNKCJE POMOCNICZE ===
    
    // Otwórz modal
    function openEventModal(startStr, endStr, event) {
        const modalTitle = document.getElementById('eventModalLabel');
        const deleteBtn = document.getElementById('deleteEventBtn');
        
        if (event) {
            // Tryb edycji
            modalTitle.textContent = 'Edytuj harmonogram';
            document.getElementById('eventTitle').value = event.title;
            document.getElementById('eventStart').value = formatDateTimeLocal(event.start);
            document.getElementById('eventEnd').value = formatDateTimeLocal(event.end);
            document.getElementById('eventMedia').value = event.extendedProps.media_id;
            deleteBtn.style.display = 'inline-block';
            currentEventId = event.id;
        } else {
            // Tryb tworzenia
            modalTitle.textContent = 'Dodaj harmonogram';
            document.getElementById('eventForm').reset();
            document.getElementById('eventStart').value = startStr ? formatDateTimeLocal(startStr) : '';
            document.getElementById('eventEnd').value = endStr ? formatDateTimeLocal(endStr) : '';
            deleteBtn.style.display = 'none';
            currentEventId = null;
        }
        
        eventModal.show();
    }
    
    // Zapisz event (CREATE lub UPDATE)
    document.getElementById('saveEventBtn').addEventListener('click', function() {
        const title = document.getElementById('eventTitle').value.trim();
        const start = document.getElementById('eventStart').value;
        const end = document.getElementById('eventEnd').value;
        const mediaId = parseInt(document.getElementById('eventMedia').value);
        
        // Walidacja
        if (!title || !start || !end || !mediaId) {
            alert('Wypełnij wszystkie pola!');
            return;
        }
        
        if (new Date(start) >= new Date(end)) {
            alert('Data końcowa musi być późniejsza niż początkowa!');
            return;
        }
        
        const eventData = {
            title: title,
            start_time: new Date(start).toISOString(),
            end_time: new Date(end).toISOString(),
            device_id: currentDeviceId,
            media_id: mediaId
        };
        
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
                throw new Error('Błąd HTTP: ' + response.status);
            }
            return response.json();
        })
        .then(data => {
            calendar.refetchEvents();
            eventModal.hide();
            alert(currentEventId ? 'Harmonogram zaktualizowany!' : 'Harmonogram utworzony!');
        })
        .catch(error => {
            console.error('Błąd zapisywania eventu:', error);
            alert('Błąd przy zapisywaniu harmonogramu');
        });
    });
    
    // Usuń event
    document.getElementById('deleteEventBtn').addEventListener('click', function() {
        if (!currentEventId) return;
        
        if (confirm('Czy na pewno chcesz usunąć ten harmonogram?')) {
            fetch(`/api/v1/events/${currentEventId}`, {
                method: 'DELETE'
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Błąd HTTP: ' + response.status);
                }
                return response.json();
            })
            .then(data => {
                calendar.refetchEvents();
                eventModal.hide();
                alert('Harmonogram usunięty!');
            })
            .catch(error => {
                console.error('Błąd usuwania eventu:', error);
                alert('Błąd przy usuwaniu harmonogramu');
            });
        }
    });
    
    // Aktualizuj daty po przeciągnięciu/zmianie rozmiaru
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
                media_id: event.extendedProps.media_id
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Błąd HTTP: ' + response.status);
            }
            return response.json();
        })
        .catch(error => {
            console.error('Błąd aktualizacji eventu:', error);
            calendar.refetchEvents(); // Przywróć oryginalny stan
            alert('Błąd przy przesuwaniu harmonogramu');
        });
    }
    
    // Formatuj datę dla input datetime-local
    function formatDateTimeLocal(dateStr) {
        const date = new Date(dateStr);
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        return `${year}-${month}-${day}T${hours}:${minutes}`;
    }
});


function updateMedia() {
    const now = new Date();
    const schedule = window.schedule || [];

    const currentEvent = schedule.find(event => {
        const start = new Date(event.start);
        const end = new Date(event.end);
        return now >= start && now < end;
    });

    const main = document.querySelector('.display-menu');
    if (!main || !currentEvent) return;

    main.innerHTML = ''; // usuń poprzednie media

    if (currentEvent.media_type === 'image') {
        const img = document.createElement('img');
        img.src = `/static/uploads/${currentEvent.filename}`;
        img.classList.add('display-img');
        main.appendChild(img);
    } else if (currentEvent.media_type === 'video') {
        const video = document.createElement('video');
        video.src = `/static/uploads/${currentEvent.filename}`;
        video.autoplay = true;
        video.loop = true;
        video.muted = true;
        video.classList.add('display-video');
        main.appendChild(video);
    }
}

// Aktualizuj co minutę (możesz dostosować)
setInterval(updateMedia, 60 * 1000);
updateMedia();
