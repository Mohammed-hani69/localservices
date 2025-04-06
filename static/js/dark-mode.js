// Dark Mode Script
document.addEventListener('DOMContentLoaded', function() {
    const toggleSwitch = document.querySelector('#darkModeToggle');
    const currentTheme = localStorage.getItem('theme');
    
    // Check for saved user preference and respect OS preference
    if (currentTheme) {
        document.body.classList.toggle('dark-mode', currentTheme === 'dark');
        toggleSwitch.checked = currentTheme === 'dark';
    } else {
        // Check if user OS prefers dark mode
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        document.body.classList.toggle('dark-mode', prefersDark);
        toggleSwitch.checked = prefersDark;
        localStorage.setItem('theme', prefersDark ? 'dark' : 'light');
    }
    
    // Switch theme function
    function switchTheme(e) {
        if (e.target.checked) {
            document.body.classList.add('dark-mode');
            localStorage.setItem('theme', 'dark');
        } else {
            document.body.classList.remove('dark-mode');
            localStorage.setItem('theme', 'light');
        }    
    }
    
    // Event listener
    toggleSwitch.addEventListener('change', switchTheme, false);
    
    // Listen for OS theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
        const newTheme = e.matches ? 'dark' : 'light';
        document.body.classList.toggle('dark-mode', e.matches);
        toggleSwitch.checked = e.matches;
        localStorage.setItem('theme', newTheme);
    });
});
