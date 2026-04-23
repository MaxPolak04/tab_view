document.addEventListener("DOMContentLoaded", function() {
    const timeElement = document.getElementById("clock-time");
    const dateElement = document.getElementById("clock-date");

    function updateClock() {
        const now = new Date();

        // Godzina: hh:mm
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');

        // Data: dd.MM.yyyy
        const day = String(now.getDate()).padStart(2, '0');
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const year = now.getFullYear();

        timeElement.textContent = `${hours}:${minutes}`;
        dateElement.textContent = `${day}.${month}.${year}`;
    }

    updateClock();
    setInterval(updateClock, 1000);
});
