document.addEventListener('DOMContentLoaded', () => {
    const toggle = document.getElementById('theme-toggle');
    if (!toggle) return;

    const html = document.documentElement;
    const lightIcon = toggle.querySelector('.light-icon');
    const darkIcon = toggle.querySelector('.dark-icon');

    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const savedTheme = localStorage.getItem('theme');

    if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
        html.classList.add('dark');
        lightIcon.style.display = 'none';
        darkIcon.style.display = 'inline';
    } else {
        html.classList.remove('dark');
        lightIcon.style.display = 'inline';
        darkIcon.style.display = 'none';
    }

    toggle.addEventListener('click', () => {
        html.classList.toggle('dark');
        const isDark = html.classList.contains('dark');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');

        lightIcon.style.display = isDark ? 'none' : 'inline';
        darkIcon.style.display = isDark ? 'inline' : 'none';
    });

    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
        if (!localStorage.getItem('theme')) {
            html.classList.toggle('dark', e.matches);
            lightIcon.style.display = e.matches ? 'none' : 'inline';
            darkIcon.style.display = e.matches ? 'inline' : 'none';
        }
    });
});
