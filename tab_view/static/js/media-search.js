// Asynchronous Live Search Script without Pagination overhead
document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('mediaSearch');
    if (!searchInput) return;

    let debounceTimer;

    searchInput.addEventListener('input', function() {
        clearTimeout(debounceTimer);

        // 300ms debounce to prevent API spamming while typing
        debounceTimer = setTimeout(() => {
            const url = new URL(window.location.href);
            url.searchParams.set('q', this.value);

            // Clean up legacy pagination parameter just in case
            url.searchParams.delete('page');

            // Fetch data asynchronously
            fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
                .then(response => response.text())
                .then(html => {
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, 'text/html');

                    // Replace grid safely
                    const newGrid = doc.getElementById('mediaGrid');
                    const currentGrid = document.getElementById('mediaGrid');

                    if (newGrid && currentGrid) {
                        currentGrid.innerHTML = newGrid.innerHTML;
                    }

                    // Update browser URL state without reload
                    window.history.pushState({ path: url.href }, '', url.href);
                })
                .catch(error => console.error('Fetch error during media search:', error));
        }, 300);
    });
});
