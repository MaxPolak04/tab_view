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

    // Zmienne stanu aplikacji
    let currentEventId = null;
    let currentPlaylist = [];
    let currentPlaylistIndex = 0;

    let isTransitioning = false;
    let isPlaying = false; // Zapobiega wielokrotnemu uruchomieniu pętli mediów
    let fallbackMedia = { filename: 'default.jpg', media_type: 'image', cache_buster: Date.now() };

    // Zmienna zapobiegająca mruganiu tego samego pliku
    let currentPlayingUrl = null;

    // ==========================================
    // 1. PĘTLA POBIERANIA DANYCH (CO 60 SEKUND)
    // ==========================================
    async function fetchState() {
        try {
            const response = await fetch(window.DEVICE_API_URL);
            if (!response.ok) throw new Error('Network response was not ok');

            const data = await response.json();
            handleStateUpdate(data);

        } catch (error) {
            console.error('Error fetching device state:', error);
            // W przypadku błędu (np. brak WiFi) nie przerywamy odtwarzania
        }
    }

    function handleStateUpdate(data) {
        if (data.status === 'event') {
            if (currentEventId !== data.event_id) {
                console.log('New event detected in background:', data.event_id);
                // Mamy całkowicie nowe wydarzenie
                currentEventId = data.event_id;
                currentPlaylist = data.playlist;
                currentPlaylistIndex = 0;
            } else {
                // To samo wydarzenie - aktualizujemy playlistę "w locie"
                // (jeśli np. w panelu admina dorzuciłeś jakiś obrazek)
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

        // Jeśli to zupełnie pierwsze uruchomienie tabletu - startujemy odtwarzanie
        if (!isPlaying) {
            playNextMedia();
        }
    }

    // ==========================================
    // 2. PĘTLA ODTWARZANIA NA EKRANIE
    // ==========================================
    function playNextMedia() {
        isPlaying = true;
        let itemToPlay = null;

        if (currentPlaylist && currentPlaylist.length > 0) {
            // Zabezpieczenie indeksu (np. gdy playlista została skrócona w panelu)
            if (currentPlaylistIndex >= currentPlaylist.length) {
                currentPlaylistIndex = 0;
            }
            itemToPlay = currentPlaylist[currentPlaylistIndex];
            currentPlaylistIndex++;
        } else {
            // Brak wydarzenia = odtwarzamy media domyślne
            itemToPlay = {
                filename: fallbackMedia.filename,
                media_type: fallbackMedia.media_type,
                cache_buster: fallbackMedia.cache_buster,
                duration: 10 // Czas wyświetlania domyślnego zdjęcia
            };
        }

        renderMedia(itemToPlay.filename, itemToPlay.media_type, itemToPlay.cache_buster, itemToPlay.duration || 10);
    }

    function renderMedia(filename, mediaType, cacheBuster, duration) {
        isTransitioning = true;

        const cacheBusterParam = cacheBuster ? `?v=${cacheBuster}` : '';
        const mediaUrl = `/static/uploads/${filename}${cacheBusterParam}`;

        // ZAPOBIEGANIE MRUGANIU (Jeśli mamy zagrać dokładnie ten sam plik)
        if (currentPlayingUrl === mediaUrl) {
            isTransitioning = false;

            if (mediaType === 'image') {
                // Czekamy ustalony czas i przechodzimy do następnego slajdu
                setTimeout(playNextMedia, duration * 1000);
            } else if (mediaType === 'video') {
                // Cofamy wideo do zera i puszczamy od nowa (płynny loop)
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

        // Fizyczna zmiana pliku z animacją
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
                // Kiedy czas obrazka mija -> graj następny (będzie czerpał z nowej pamięci)
                setTimeout(playNextMedia, duration * 1000);
            };

            img.onerror = () => {
                console.error('Failed to load image:', mediaUrl);
                isTransitioning = false;
                setTimeout(playNextMedia, 5000); // W razie błędu czekamy 5s i omijamy
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
                // Kiedy wideo dojdzie do końca -> graj następne (będzie czerpał z nowej pamięci)
                playNextMedia();
            };

            video.onerror = () => {
                console.error('Failed to load video:', mediaUrl);
                isTransitioning = false;
                setTimeout(playNextMedia, 5000); // W razie błędu czekamy 5s i omijamy
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

    // === INITIALIZATION ===
    console.log('=== DISPLAY ENGINE STARTED (1-MINUTE POLLING) ===');

    // Pierwsze ręczne pobranie danych na start
    fetchState();

    // Ustawienie zegara: twardo pytaj API co równe 60 sekund w tle
    setInterval(fetchState, 60 * 1000);

})();
