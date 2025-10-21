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


document.addEventListener('DOMContentLoaded', function() {
    const calendarEl = document.getElementById('calendar');
    
    // Sprawdź czy element kalendarza istnieje na stronie
    if (!calendarEl) return;
    
    const calendar = new FullCalendar.Calendar(calendarEl, {
        // Podstawowe ustawienia
        initialView: 'dayGridMonth',
        locale: 'pl',
        
        // Nagłówek z przyciskami
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        
        // Włącz interakcje
        editable: true,
        selectable: true,
        
        // POBIERANIE EVENTÓW Z API
        events: function(info, successCallback, failureCallback) {
            fetch('/api/v1/events/')
                .then(response => response.json())
                .then(data => {
                    // Twoje API zwraca już poprawny format ISO
                    const events = data.map(event => ({
                        id: event.id,
                        title: event.title,
                        start: event.start_time,
                        end: event.end_time,
                        extendedProps: {
                            device_id: event.device_id,
                            media_id: event.media_id
                        }
                    }));
                    successCallback(events);
                })
                .catch(error => {
                    console.error('Błąd pobierania eventów:', error);
                    failureCallback(error);
                });
        },
        
        // TWORZENIE NOWEGO EVENTU (kliknięcie w pusty obszar)
        select: function(info) {
            const title = prompt('Nazwa eventu:');
            if (title) {
                fetch('/api/v1/events/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        title: title,
                        start_time: info.startStr,
                        end_time: info.endStr,
                        device_id: 1,  // Później dodasz wybór device
                        media_id: 1    // Później dodasz wybór media
                    })
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Błąd HTTP: ' + response.status);
                    }
                    return response.json();
                })
                .then(data => {
                    calendar.refetchEvents();
                    alert('Event utworzony!');
                })
                .catch(error => {
                    console.error('Błąd tworzenia eventu:', error);
                    alert('Błąd przy tworzeniu eventu');
                });
            }
            calendar.unselect();
        },
        
        // EDYCJA EVENTU (kliknięcie w istniejący event)
        eventClick: function(info) {
            const newTitle = prompt('Nowa nazwa:', info.event.title);
            if (newTitle && newTitle !== info.event.title) {
                fetch(`/api/v1/events/${info.event.id}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        title: newTitle,
                        start_time: info.event.start.toISOString(),
                        end_time: info.event.end.toISOString(),
                        device_id: info.event.extendedProps.device_id,
                        media_id: info.event.extendedProps.media_id
                    })
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Błąd HTTP: ' + response.status);
                    }
                    return response.json();
                })
                .then(data => {
                    info.event.setProp('title', newTitle);
                    alert('Event zaktualizowany!');
                })
                .catch(error => {
                    console.error('Błąd aktualizacji eventu:', error);
                    alert('Błąd przy aktualizacji eventu');
                });
            }
        },
        
        // PRZECIĄGANIE EVENTU (zmiana daty)
        eventDrop: function(info) {
            fetch(`/api/v1/events/${info.event.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    title: info.event.title,
                    start_time: info.event.start.toISOString(),
                    end_time: info.event.end.toISOString(),
                    device_id: info.event.extendedProps.device_id,
                    media_id: info.event.extendedProps.media_id
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Błąd HTTP: ' + response.status);
                }
                return response.json();
            })
            .then(data => {
                console.log('Event przesunięty');
            })
            .catch(error => {
                console.error('Błąd przy przesuwaniu eventu:', error);
                info.revert(); // Cofnij zmianę jeśli błąd
                alert('Błąd przy przesuwaniu eventu');
            });
        },
        
        // ZMIANA ROZMIARU EVENTU
        eventResize: function(info) {
            fetch(`/api/v1/events/${info.event.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    title: info.event.title,
                    start_time: info.event.start.toISOString(),
                    end_time: info.event.end.toISOString(),
                    device_id: info.event.extendedProps.device_id,
                    media_id: info.event.extendedProps.media_id
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Błąd HTTP: ' + response.status);
                }
                return response.json();
            })
            .then(data => {
                console.log('Rozmiar eventu zmieniony');
            })
            .catch(error => {
                console.error('Błąd przy zmianie rozmiaru:', error);
                info.revert(); // Cofnij zmianę jeśli błąd
                alert('Błąd przy zmianie rozmiaru');
            });
        }
    });
    
    calendar.render();
});


setTimeout(() => {
    document.querySelectorAll('.flash-overlay .alert').forEach(alert => {
        alert.classList.add('fade-out');
        setTimeout(() => alert.remove(), 500);
    });
}, 3000);

