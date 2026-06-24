document.addEventListener("DOMContentLoaded", function() {
    'use strict';

    const timeElement = document.getElementById("clock-time");
    const dateElement = document.getElementById("clock-date");

    if (timeElement && dateElement) {
        /**
         * Updates the clock and date elements with current system time.
         * Pure text mutation, zero DOM layout thrashing.
         */
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
});
