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
    let currentEventTitle = null;
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

        updateWeatherWidget(data.weather, data.show_weather);

        if (data.status === 'event') {
            if (currentEventId !== data.event_id) {
                console.log('New event detected in background:', data.event_id);
                currentEventId = data.event_id;
                currentEventTitle = data.event_title;
                currentPlaylist = data.playlist;
                currentPlaylistIndex = 0;
            } else {
                currentPlaylist = data.playlist;
                currentEventTitle = data.event_title;
            }
        } else if (data.status === 'default') {
            if (currentEventId !== null) {
                console.log('Event ended, scheduled fallback to default media.');
                currentEventId = null;
                currentEventTitle = null;
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

        if (currentEventId !== null && (!currentPlaylist || currentPlaylist.length === 0)) {
            itemToPlay = {
                media_type: 'text_only',
                title: currentEventTitle || "No Title",
                duration: 60
            };
        }
        else if (currentPlaylist && currentPlaylist.length > 0) {
            if (currentPlaylistIndex >= currentPlaylist.length) {
                currentPlaylistIndex = 0;
            }
            itemToPlay = currentPlaylist[currentPlaylistIndex];
            currentPlaylistIndex++;
        }
        else {
            itemToPlay = {
                filename: fallbackMedia.filename,
                media_type: fallbackMedia.media_type,
                cache_buster: fallbackMedia.cache_buster,
                duration: 10
            };
        }

        renderMedia(itemToPlay);
    }

    function renderMedia(item) {
        isTransitioning = true;

        let mediaUrl = null;
        let isTextOnly = item.media_type === 'text_only';

        if (isTextOnly) {
            mediaUrl = `text_only_${item.title}`;
        } else {
            const cacheBusterParam = item.cache_buster ? `?v=${item.cache_buster}` : '';
            mediaUrl = `/static/uploads/${item.filename}${cacheBusterParam}`;
        }

        if (currentPlayingUrl === mediaUrl) {
            isTransitioning = false;

            if (isTextOnly || item.media_type === 'image') {
                setTimeout(playNextMedia, item.duration * 1000);
            } else if (item.media_type === 'video') {
                const video = main.querySelector('video');
                if (video) {
                    video.currentTime = 0;
                    video.play().catch(e => console.error("Video replay error:", e));
                } else {
                    injectNewMedia(item, mediaUrl);
                }
            }
            return;
        }

        currentPlayingUrl = mediaUrl;

        if (main.firstChild) {
            main.firstChild.style.animation = 'fadeOut 0.3s ease-out';
            setTimeout(() => {
                main.innerHTML = '';
                injectNewMedia(item, mediaUrl);
            }, 300);
        } else {
            injectNewMedia(item, mediaUrl);
        }
    }

    function injectNewMedia(item, mediaUrl) {
        if (item.media_type === 'text_only') {
            const textContainer = document.createElement('div');

            textContainer.style.width = '100vw';
            textContainer.style.height = '100vh';
            textContainer.style.display = 'flex';
            textContainer.style.alignItems = 'center';
            textContainer.style.justifyContent = 'center';
            textContainer.style.backgroundColor = '#212121';
            textContainer.style.animation = 'fadeIn 0.5s ease-in';
            textContainer.style.padding = '5vw';
            textContainer.style.boxSizing = 'border-box';
            textContainer.style.overflow = 'hidden';

            const textElement = document.createElement('h1');
            textElement.textContent = item.title;
            textElement.style.fontSize = '8vw';
            textElement.style.color = '#ffffff';
            textElement.style.textAlign = 'center';
            textElement.style.fontFamily = '"Montserrat", sans-serif';
            textElement.style.fontWeight = 'bold';
            textElement.style.wordBreak = 'break-word';
            textElement.style.margin = '0';

            textContainer.appendChild(textElement);
            main.appendChild(textContainer);

            isTransitioning = false;
            setTimeout(playNextMedia, item.duration * 1000);

        } else if (item.media_type === 'image') {
            const img = document.createElement('img');
            img.src = mediaUrl;
            img.classList.add('display-img');
            img.style.animation = 'fadeIn 0.5s ease-in';

            img.onload = () => {
                isTransitioning = false;
                setTimeout(playNextMedia, item.duration * 1000);
            };

            img.onerror = () => {
                console.error('Failed to load image:', mediaUrl);
                isTransitioning = false;
                setTimeout(playNextMedia, 5000);
            };

            main.appendChild(img);

        } else if (item.media_type === 'video') {
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

    function updateWeatherWidget(weatherData, shouldShow) {
        const container = document.getElementById('weather-widget');
        if (!shouldShow || !weatherData || weatherData.length === 0) {
            container.classList.add('d-none');
            return;
        }

        // Zastosowanie jednostek vh i vw w miejsce klas typograficznych Bootstrapa
        let html = `
            <div class="d-flex flex-column text-white text-center"
                 style="gap: 4vh; padding: 3vh 3vh 3vh 2vh; background: rgba(0,0,0,0.3); backdrop-filter: blur(12px); border-radius: 0 4vh 4vh 0; border: 1px solid rgba(255,255,255,0.1); border-left: none; box-shadow: 5px 5px 15px rgba(0,0,0,0.2);">`;

        weatherData.forEach(day => {
            html += `
                <div>
                    <div class="text-uppercase fw-bold opacity-75" style="font-size: 2vh; letter-spacing: 0.2vw; margin-bottom: 1vh;">${day.day}</div>
                    <i class="bi ${day.icon} d-block" style="font-size: 7vh; filter: drop-shadow(0 4px 6px rgba(0,0,0,0.4)); margin: 1.5vh 0;"></i>
                    <div class="fw-bold" style="font-size: 5vh; line-height: 1; text-shadow: 0 2px 4px rgba(0,0,0,0.3);">${day.temp}°C</div>
                    <div class="opacity-90 fw-medium" style="font-size: 2.5vh; margin-top: 1.5vh;">
                        <i class="bi bi-wind" style="margin-right: 0.5vw;"></i>${day.wind}<span style="font-size: 1.8vh; margin-left: 0.2vw;"> km/h</span>
                    </div>
                </div>
            `;
        });
        html += '</div>';

        container.innerHTML = html;
        container.classList.remove('d-none');
    }

    console.log('=== DISPLAY ENGINE STARTED (1-MINUTE POLLING) ===');

    fetchState();
    setInterval(fetchState, 60 * 1000);

})();
