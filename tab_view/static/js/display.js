

(function() {
    'use strict';
    
    // Check if the data is needed
    if (typeof window.schedule === 'undefined' || typeof window.defaultMedia === 'undefined') {
        console.error('No schedule data or default media');
        return;
    }
    
    const main = document.querySelector('.display-menu');
    if (!main) {
        console.error('Element .display-menu not found');
        return;
    }
    
    // Application status
    let currentMediaUrl = null;
    let currentEventId = null;
    let currentPlaylistIndex = 0;
    let mediaRotationTimer = null;
    let checkScheduleTimer = null;
    
    /**
     * Checks the schedule and activates the appropriate media
     */
    function checkSchedule() {
        const now = new Date();
        const schedule = window.schedule || [];
        
        // Find an active event
        const activeEvent = schedule.find(event => {
            const start = new Date(event.start);
            const end = new Date(event.end);
            return now >= start && now < end;
        });
        
        if (activeEvent) {
            // If this is a new event, reset the playlist.
            if (currentEventId !== activeEvent.id) {
                console.log('New active event:', activeEvent.title);
                currentEventId = activeEvent.id;
                currentPlaylistIndex = 0;
                startPlaylist(activeEvent.media_playlist);
            }
            // If it's the same event, continue the playlist (do not reset)
        } else {
            // No active event - display default media
            if (currentEventId !== null || currentMediaUrl === null) {
                console.log('No active event - switching to default media');
                currentEventId = null;
                stopPlaylist();
                
                // Check if there are default media
                if (window.defaultMedia && window.defaultMedia.filename) {
                    displaySingleMedia(window.defaultMedia.filename, window.defaultMedia.media_type);
                } else {
                    // Fallback on default.jpg
                    console.warn('No default media - loading default.jpg');
                    displaySingleMedia('default.jpg', 'image');
                }
            }
        }
    }
    
    /**
     * Starts the media playlist
     */
    function startPlaylist(playlist) {
        if (!playlist || playlist.length === 0) {
            console.warn('Empty playlist');
            displaySingleMedia(window.defaultMedia.filename, window.defaultMedia.media_type);
            return;
        }
        
        // Stop the previous rotation
        stopPlaylist();
        
        // Display the first media
        displayPlaylistItem(playlist, 0);
    }
    
    /**
     * Displays a specific item from the playlist
     */
    function displayPlaylistItem(playlist, index) {
        if (index >= playlist.length) {
            index = 0; // Start from the beginning
        }
        
        const item = playlist[index];
        currentPlaylistIndex = index;
        
        console.log(`Playlist [${index + 1}/${playlist.length}]:`, item.filename);
        
        if (item.media_type === 'image') {
            // Image - display for a specified period of time
            displayMedia(item.filename, item.media_type);
            
            const duration = (item.duration || 10) * 1000; // Default 10 seconds
            mediaRotationTimer = setTimeout(() => {
                displayPlaylistItem(playlist, index + 1);
            }, duration);
            
        } else if (item.media_type === 'video') {
            // Video - wait until it finishes
            displayMedia(item.filename, item.media_type, () => {
                // Callback after video finish
                displayPlaylistItem(playlist, index + 1);
            });
        }
    }
    
    /**
     * Stops media rotation
     */
    function stopPlaylist() {
        if (mediaRotationTimer) {
            clearTimeout(mediaRotationTimer);
            mediaRotationTimer = null;
        }
    }
    
    /**
     * Displays single media (for the device's default media)
     */
    function displaySingleMedia(filename, mediaType) {
        if (!filename) {
            console.error('No file name to display');
            showError('No media to display');
            return;
        }
        displayMedia(filename, mediaType);
    }
    
    /**
     * Displays media (image or video) with fadeIn animation support
     */
    function displayMedia(filename, mediaType, onVideoEnd) {
        const mediaUrl = `/static/uploads/${filename}`;
        
        // Check if they are the same media (avoid flickering)
        if (currentMediaUrl === mediaUrl) {
            console.log('The same media - I\'m ignoring the change');
            return;
        }
        
        currentMediaUrl = mediaUrl;
        
        // Clear previous media with fadeOut animation
        if (main.firstChild) {
            main.firstChild.style.animation = 'fadeOut 0.3s ease-out';
            setTimeout(() => {
                main.innerHTML = '';
                renderMedia();
            }, 300);
        } else {
            renderMedia();
        }
        
        function renderMedia() {
            if (mediaType === 'image') {
                const img = document.createElement('img');
                img.src = mediaUrl;
                img.classList.add('display-img');
                img.alt = 'Display content';
                img.style.animation = 'fadeIn 0.5s ease-in';
                
                img.onerror = function() {
                    console.error('Image loading error:', filename);
                    
                    // Try loading default.jpg
                    if (filename !== 'default.jpg') {
                        console.log('I\'m trying to load default.jpg');
                        this.src = '/static/uploads/default.jpg';
                        this.onerror = function() {
                            showError('No image can be loaded');
                        };
                    } else {
                        showError('The image cannot be loaded');
                    }
                };
                
                main.appendChild(img);
                
            } else if (mediaType === 'video') {
                const video = document.createElement('video');
                video.src = mediaUrl;
                video.autoplay = true;
                video.muted = true;
                video.classList.add('display-video');
                video.style.animation = 'fadeIn 0.5s ease-in';
                
                // Do NOT set a loop - we need to know when it will end.
                
                video.onerror = function() {
                    console.error('Video loading error:', filename);
                    showError('Unable to load video');
                };
                
                // Callback after video completion
                if (onVideoEnd) {
                    video.addEventListener('ended', onVideoEnd);
                } else {
                    // If it's the default video, loop it.
                    video.loop = true;
                }
                
                main.appendChild(video);
            } else {
                console.error('Unknown media type:', mediaType);
                showError('Unknown media type');
            }
        }
    }
    
    /**
     * Displays an error message
     */
    function showError(message) {
        main.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: center; height: 100vh; font-size: 2rem; color: #dc3545;">
                <p>${message}</p>
            </div>
        `;
        currentMediaUrl = null;
    }
    
    /**
     * Debugging
     */
    function debugSchedule() {
        console.log('=== SCHEDULE DEBUG ===');
        console.log('Current time:', new Date().toISOString());
        console.log('Number of events:', window.schedule.length);
        window.schedule.forEach((event, index) => {
            console.log(`Event ${index + 1}:`, {
                id: event.id,
                title: event.title,
                start: event.start,
                end: event.end,
                playlist_length: event.media_playlist?.length || 0
            });
            if (event.media_playlist) {
                event.media_playlist.forEach((media, i) => {
                    console.log(`  Media ${i + 1}:`, media);
                });
            }
        });
        console.log('Default media:', window.defaultMedia);
        console.log('========================');
    }
    
    // === INITIALIZATION ===
    
    console.log('=== DISPLAY INITIALIZATION ===');
    console.log('Default media:', window.defaultMedia);
    console.log('Schedule:', window.schedule);
    
    debugSchedule();
    checkSchedule();
    
    // If nothing is still displayed after checkSchedule, force the default media.
    setTimeout(() => {
        if (!main.firstChild) {
            console.warn('No elements in main - forcing default media');
            if (window.defaultMedia && window.defaultMedia.filename) {
                displaySingleMedia(window.defaultMedia.filename, window.defaultMedia.media_type);
            } else {
                displaySingleMedia('default.jpg', 'image');
            }
        }
    }, 1000);
    
    // Check the schedule every 30 seconds
    checkScheduleTimer = setInterval(checkSchedule, 30 * 1000);
    
    // Check when changing the visibility of the tab
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden) {
            console.log('Active tab - checking the schedule');
            checkSchedule();
        }
    });
    
    // Clear timers when closing the page
    window.addEventListener('beforeunload', function() {
        stopPlaylist();
        if (checkScheduleTimer) {
            clearInterval(checkScheduleTimer);
        }
    });
    
})();