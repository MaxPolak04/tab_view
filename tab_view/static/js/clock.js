document.addEventListener("DOMContentLoaded", function() {
    'use strict';

    const timeElement = document.getElementById("clock-time");
    const dateElement = document.getElementById("clock-date");

    if (timeElement && dateElement) {
        function updateClock() {
            const now = new Date();

            const hours = String(now.getHours()).padStart(2, '0');
            const minutes = String(now.getMinutes()).padStart(2, '0');

            const day = String(now.getDate()).padStart(2, '0');
            const month = String(now.getMonth() + 1).padStart(2, '0');
            const year = now.getFullYear();

            timeElement.textContent = `${hours}:${minutes}`;
            dateElement.textContent = `${day}.${month}.${year}`;
        }

        updateClock();
        setInterval(updateClock, 1000);
    }

    const clock = document.getElementById('system-clock-overlay');
    const weather = document.getElementById('weather-widget');

    if (clock) {
        function syncTopEdge() {
            if (weather && !weather.classList.contains('d-none') && weather.children.length > 0) {
                const weatherRect = weather.getBoundingClientRect();
                clock.style.top = `${weatherRect.top}px`;
                clock.style.transform = 'none';
            } else {
                clock.style.top = '15%';
                clock.style.transform = 'translateY(-50%)';
            }
        }

        syncTopEdge();

        if (weather) {
            const observer = new MutationObserver(() => requestAnimationFrame(syncTopEdge));
            observer.observe(weather, {
                childList: true,
                attributes: true,
                attributeFilter: ['class']
            });
            window.addEventListener('resize', syncTopEdge);
        }
    }
});
