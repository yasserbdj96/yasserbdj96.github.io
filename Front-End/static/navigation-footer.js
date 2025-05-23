// Load navigation
fetch('./templates/navigation.html')
    .then(response => response.text())
    .then(data => {
        document.getElementById('nav-placeholder').innerHTML = data;
        initializeMobileMenu();
    })
    .catch(error => console.error('Error loading navigation:', error));

// Load footer
fetch('./templates/footer.html')
    .then(response => response.text())
    .then(data => {
        const currentYear = new Date().getFullYear();
        const updatedData = data.replace(
            /&copy;.*?<\/p>/i,
            `&copy; ${currentYear} yasserbdj96. All rights reserved.</p>`
        );
        document.getElementById('footer-placeholder').innerHTML = updatedData;
    })
    .catch(error => console.error('Error loading footer:', error));

// Mobile menu initialization
function initializeMobileMenu() {
    const hamburger = document.querySelector('.hamburger');
    const navLinks = document.querySelector('.nav-links');

    if (!hamburger || !navLinks) {
        console.error('Mobile menu elements not found!');
        return;
    }

    // Update ARIA attributes
    const updateAria = () => {
        const isActive = navLinks.classList.contains('active');
        hamburger.setAttribute('aria-expanded', isActive);
        navLinks.setAttribute('aria-hidden', !isActive);
    };

    hamburger.addEventListener('click', (e) => {
        e.stopPropagation();
        hamburger.classList.toggle('active');
        navLinks.classList.toggle('active');
        updateAria();
    });

    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.nav-links') && !e.target.closest('.hamburger')) {
            hamburger.classList.remove('active');
            navLinks.classList.remove('active');
            updateAria();
        }
    });

    // Close menu on link click
    navLinks.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', () => {
            hamburger.classList.remove('active');
            navLinks.classList.remove('active');
            updateAria();
        });
    });
}
