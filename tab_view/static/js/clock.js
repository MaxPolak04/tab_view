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
    const weatherLeft = document.getElementById('weather-widget-left');
    const weatherRight = document.getElementById('weather-widget-right');

    if (clock) {
        function syncLayout() {
            // 1. Synchronize clock's top edge with the left weather widget to maintain screen symmetry
            if (weatherLeft && !weatherLeft.classList.contains('d-none') && weatherLeft.children.length > 0) {
                const leftRect = weatherLeft.getBoundingClientRect();
                clock.style.top = `${leftRect.top}px`;
                clock.style.transform = 'none';
            } else {
                clock.style.top = '15%';
                clock.style.transform = 'translateY(-50%)';
            }

            // 2. Position the right weather widget directly under the clock with a clean, tight gap
            if (weatherRight) {
                if (!clock.classList.contains('d-none')) {
                    const clockRect = clock.getBoundingClientRect();
                    const gap = window.innerHeight * 0.015; // Tight 1.5vh gap for seamless visual grouping
                    weatherRight.style.top = `${clockRect.bottom + gap}px`;
                } else {
                    weatherRight.style.top = '25vh';
                }

                // Enforce perfect width consistency with the main clock panel
                const innerDiv = weatherRight.querySelector('div');
                if (innerDiv) {
                    innerDiv.style.width = '26vh';
                    innerDiv.style.boxSizing = 'border-box';
                }
            }
        }

        // Execute initial layout alignment
        syncLayout();

        // Setup MutationObservers to handle dynamic updates from the core state engine polling loop
        const observer = new MutationObserver(() => requestAnimationFrame(syncLayout));

        if (weatherLeft) {
            observer.observe(weatherLeft, {
                childList: true,
                attributes: true,
                attributeFilter: ['class']
            });
        }

        if (weatherRight) {
            observer.observe(weatherRight, {
                childList: true,
                attributes: true,
                attributeFilter: ['class']
            });
        }

        // Safely observe clock class updates without causing recursive layout loops
        observer.observe(clock, {
            attributes: true,
            attributeFilter: ['class']
        });

        window.addEventListener('resize', syncLayout);
    }
});
