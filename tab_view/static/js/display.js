(function() {
    'use strict';

    if (typeof window.DEVICE_API_URL === 'undefined') {
        console.error('DEVICE_API_URL is not defined');
        return;
    }

    const main = document.querySelector('.display-menu');
    if (!main) {
        console.error('Element .display-menu not found');
        return;
    }

    const clockOverlay = document.getElementById('system-clock-overlay');

    let currentEventId = null;
    let currentPlaylist = [];
    let currentPlaylistIndex = 0;

    let isTransitioning = false;
    let isPlaying = false;
    let fallbackMedia = { filename: 'default.jpg', media_type: 'image', cache_buster: Date.now() };

    let currentPlayingUrl = null;

    async function fetchState() {
        try {
            const response = await fetch(window.DEVICE_API_URL);
            if (!response.ok) throw new Error('Network response was not ok');

            const data = await response.json();
            handleStateUpdate(data);

        } catch (error) {
            console.error('Error fetching device state:', error);
        }
    }

    function handleStateUpdate(data) {
        if (clockOverlay) {
            if (data.show_clock === true) {
                clockOverlay.classList.remove('d-none');
            } else {
                clockOverlay.classList.add('d-none');
            }
        }

        if (data.status === 'event') {
            if (currentEventId !== data.event_id) {
                console.log('New event detected in background:', data.event_id);
                currentEventId = data.event_id;
                currentPlaylist = data.playlist;
                currentPlaylistIndex = 0;
            } else {
                currentPlaylist = data.playlist;
            }
        } else if (data.status === 'default') {
            if (currentEventId !== null) {
                console.log('Event ended, scheduled fallback to default media.');
                currentEventId = null;
                currentPlaylist = [];
                currentPlaylistIndex = 0;
            }
            if (data.default_media) {
                fallbackMedia = data.default_media;
            }
        }

        if (!isPlaying) {
            playNextMedia();
        }
    }

    function playNextMedia() {
        isPlaying = true;
        let itemToPlay = null;

        if (currentPlaylist && currentPlaylist.length > 0) {
            if (currentPlaylistIndex >= currentPlaylist.length) {
                currentPlaylistIndex = 0;
            }
            itemToPlay = currentPlaylist[currentPlaylistIndex];
            currentPlaylistIndex++;
        } else {
            itemToPlay = {
                filename: fallbackMedia.filename,
                media_type: fallbackMedia.media_type,
                cache_buster: fallbackMedia.cache_buster,
                duration: 10
            };
        }

        renderMedia(itemToPlay.filename, itemToPlay.media_type, itemToPlay.cache_buster, itemToPlay.duration || 10);
    }

    function renderMedia(filename, mediaType, cacheBuster, duration) {
        isTransitioning = true;

        const cacheBusterParam = cacheBuster ? `?v=${cacheBuster}` : '';
        const mediaUrl = `/static/uploads/${filename}${cacheBusterParam}`;

        if (currentPlayingUrl === mediaUrl) {
            isTransitioning = false;

            if (mediaType === 'image') {
                setTimeout(playNextMedia, duration * 1000);
            } else if (mediaType === 'video') {
                const video = main.querySelector('video');
                if (video) {
                    video.currentTime = 0;
                    video.play().catch(e => console.error("Video replay error:", e));
                } else {
                    injectNewMedia(mediaUrl, mediaType, duration);
                }
            }
            return;
        }

        currentPlayingUrl = mediaUrl;

        if (main.firstChild) {
            main.firstChild.style.animation = 'fadeOut 0.3s ease-out';
            setTimeout(() => {
                main.innerHTML = '';
                injectNewMedia(mediaUrl, mediaType, duration);
            }, 300);
        } else {
            injectNewMedia(mediaUrl, mediaType, duration);
        }
    }

    function injectNewMedia(mediaUrl, mediaType, duration) {
        if (mediaType === 'image') {
            const img = document.createElement('img');
            img.src = mediaUrl;
            img.classList.add('display-img');
            img.style.animation = 'fadeIn 0.5s ease-in';

            img.onload = () => {
                isTransitioning = false;
                setTimeout(playNextMedia, duration * 1000);
            };

            img.onerror = () => {
                console.error('Failed to load image:', mediaUrl);
                isTransitioning = false;
                setTimeout(playNextMedia, 5000);
            };

            main.appendChild(img);

        } else if (mediaType === 'video') {
            const video = document.createElement('video');
            video.src = mediaUrl;
            video.autoplay = true;
            video.muted = true;
            video.classList.add('display-video');
            video.style.animation = 'fadeIn 0.5s ease-in';

            video.onplaying = () => {
                isTransitioning = false;
            };

            video.onended = () => {
                playNextMedia();
            };

            video.onerror = () => {
                console.error('Failed to load video:', mediaUrl);
                isTransitioning = false;
                setTimeout(playNextMedia, 5000);
            };

            main.appendChild(video);

            const playPromise = video.play();
            if (playPromise !== undefined) {
                playPromise.catch(error => {
                    console.error("Autoplay prevented:", error);
                    isTransitioning = false;
                    setTimeout(playNextMedia, 5000);
                });
            }
        }
    }

    console.log('=== DISPLAY ENGINE STARTED (1-MINUTE POLLING) ===');

    fetchState();
    setInterval(fetchState, 60 * 1000);

})();
