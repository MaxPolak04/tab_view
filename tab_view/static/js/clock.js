(function() {
    'use strict';

    const STORAGE_KEY = 'tabview_server_time_offset';
    let timeOffset = 0;

    // Restore cached offset from localStorage if available (for offline boot or refresh)
    try {
        const savedOffset = localStorage.getItem(STORAGE_KEY);
        if (savedOffset !== null) {
            const parsed = parseInt(savedOffset, 10);
            if (!isNaN(parsed)) {
                timeOffset = parsed;
            }
        }
    } catch (e) {
        // localStorage might be unavailable or restricted in some kiosk environments
    }

    /**
     * Synchronize time with the application server.
     * Calculates the offset between the server's NTP clock and the local client clock.
     * @param {string|number|Date} serverTime - Server ISO string, timestamp in ms, or Date object
     * @param {number} [latencyMs=0] - Estimated round-trip latency in milliseconds
     */
    function syncServerTime(serverTime, latencyMs) {
        if (!serverTime) return;

        let serverTimeMs;
        if (typeof serverTime === 'number') {
            serverTimeMs = serverTime;
        } else if (serverTime instanceof Date) {
            serverTimeMs = serverTime.getTime();
        } else if (typeof serverTime === 'string') {
            serverTimeMs = new Date(serverTime).getTime();
        }

        if (isNaN(serverTimeMs)) return;

        // Account for half of round-trip network latency if sensible (< 10 seconds)
        if (typeof latencyMs === 'number' && latencyMs > 0 && latencyMs < 10000) {
            serverTimeMs += Math.round(latencyMs / 2);
        }

        timeOffset = serverTimeMs - Date.now();

        try {
            localStorage.setItem(STORAGE_KEY, timeOffset.toString());
        } catch (e) {
            // Ignore storage write errors
        }

        updateClock();
    }

    // Expose synchronization function globally for display.js or external callers
    window.syncServerTime = syncServerTime;

    let timeElement = null;
    let dateElement = null;

    /**
     * Updates the clock and date elements with current synchronized time.
     * Runs completely autonomously even if server connection is lost.
     * Pure text mutation, zero DOM layout thrashing.
     */
    function updateClock() {
        if (!timeElement || !dateElement) {
            timeElement = document.getElementById("clock-time");
            dateElement = document.getElementById("clock-date");
            if (!timeElement || !dateElement) return;
        }

        const now = new Date(Date.now() + timeOffset);

        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');

        const day = String(now.getDate()).padStart(2, '0');
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const year = now.getFullYear();

        timeElement.textContent = `${hours}:${minutes}`;
        dateElement.textContent = `${day}.${month}.${year}`;
    }

    document.addEventListener("DOMContentLoaded", function() {
        timeElement = document.getElementById("clock-time");
        dateElement = document.getElementById("clock-date");

        if (timeElement && dateElement) {
            // Check for initial server time passed from template via data-attribute or window
            const overlay = document.getElementById("system-clock-overlay");
            const initialTime = (overlay && overlay.getAttribute("data-server-time")) || window.INITIAL_SERVER_TIME;

            if (initialTime) {
                syncServerTime(initialTime);
            }

            updateClock();
            setInterval(updateClock, 1000);
        }
    });
})();
