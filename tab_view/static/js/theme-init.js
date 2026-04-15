(function() {
    const storedTheme = localStorage.getItem('theme');
    const getPreferredTheme = () => {
        if (storedTheme) {
            return storedTheme;
        }
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    };
    document.documentElement.setAttribute('data-bs-theme', getPreferredTheme());
})();
