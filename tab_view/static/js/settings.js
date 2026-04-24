document.addEventListener('DOMContentLoaded', () => {
    const clockEl = document.getElementById('live-server-clock');
    if (!clockEl) return;

    const serverTimeStr = clockEl.getAttribute('data-server-time');
    if (!serverTimeStr) return;

    let serverTime = new Date(serverTimeStr);

    function updateDisplay() {
        serverTime.setSeconds(serverTime.getSeconds() + 1);

        const hh = String(serverTime.getHours()).padStart(2, '0');
        const mm = String(serverTime.getMinutes()).padStart(2, '0');
        const ss = String(serverTime.getSeconds()).padStart(2, '0');

        const dateStr = serverTime.toISOString().split('T')[0];

        clockEl.textContent = `${dateStr} ${hh}:${mm}:${ss}`;
    }

    updateDisplay();
    setInterval(updateDisplay, 1000);
});
