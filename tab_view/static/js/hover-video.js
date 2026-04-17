document.addEventListener('DOMContentLoaded', () => {
    // Select all cards that might contain a video
    const cards = document.querySelectorAll('.card');

    cards.forEach(card => {
        // Look for the video ONLY inside this specific card
        const video = card.querySelector('.hover-video');

        // If the card has a video, attach the hover events to the entire card
        if (video) {
            card.addEventListener('mouseenter', () => {
                video.play().catch(err => {
                    console.warn('Video playback prevented by browser:', err);
                });
            });

            card.addEventListener('mouseleave', () => {
                video.pause();
                video.currentTime = 0; // Rewind to start
            });
        }
    });
});
