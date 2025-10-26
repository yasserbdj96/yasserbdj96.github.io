// Theme Toggle
function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    const icon = document.getElementById('theme-icon');
    icon.className = newTheme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
}

// Load saved theme
const savedTheme = localStorage.getItem('theme') || 'dark';
document.documentElement.setAttribute('data-theme', savedTheme);
if (document.getElementById('theme-icon')) {
    document.getElementById('theme-icon').className = savedTheme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
}

// Data storage
let appData = null;

// Helper to load a local JSON file safely
async function tryLocalJSON(localPath, inlineFallback = {}) {
    try {
        const res = await fetch(localPath);
        if (!res.ok) throw new Error('Local fetch failed: ' + res.status);
        return await res.json();
    } catch (err) {
        console.warn('Local JSON load failed for', localPath, err);
        return inlineFallback;
    }
}

// Load data
async function loadData() {
    if (appData) return appData;

    const inlineFallback = {}; // Add any inline fallback data if needed
    
    try {
            // Try remote first
            try {
                const response = await fetch('https://yasserbdj96.pythonanywhere.com/data.json');
                if (!response.ok) throw new Error('Remote fetch failed: ' + response.status);
                appData = await response.json();
                return appData;
            } catch (remoteError) {
                console.warn('Remote fetch failed; trying local file.', remoteError);
                // Try local file (parsed JSON)
                const local = await tryLocalJSON('./data.json', inlineFallback);
                appData = local;
                return appData;
            }
    } catch (error) {
        console.error('Error loading data fallback:', error);
        return { projects: [], blogPosts: [] };
    }
}

// Navigation scroll effect
window.addEventListener('scroll', () => {
    const navbar = document.getElementById('navbar');
    if (window.scrollY > 50) {
        navbar.classList.add('scrolled');
    } else {
        navbar.classList.remove('scrolled');
    }
});

// Mobile menu toggle
const hamburger = document.querySelector('.hamburger');
const navRight = document.querySelector('.nav-right');

if (hamburger && navRight) {
    hamburger.addEventListener('click', () => {
        hamburger.classList.toggle('active');
        navRight.classList.toggle('active');
    });
}

// Close mobile menu on link click
document.querySelectorAll('.nav-links a').forEach(link => {
    link.addEventListener('click', () => {
        if (hamburger && navRight) {
            hamburger.classList.remove('active');
            navRight.classList.remove('active');
        }
    });
});

// Smooth scroll
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            const offsetTop = target.offsetTop - 80;
            window.scrollTo({
                top: offsetTop,
                behavior: 'smooth'
            });
        }
    });
});

// Initialize projects
async function initProjects() {
    const data = await loadData();
    const projects = data.projects || [];
    
    if (projects.length === 0) {
        document.getElementById('projects-grid').innerHTML = `
            <div class="empty-state">
                <i class="fas fa-folder-open"></i>
                <h3>No Projects Yet</h3>
                <p>Check back soon for exciting projects!</p>
            </div>
        `;
        document.getElementById('tech-filters').style.display = 'none';
        return;
    }
    
    // Create tech filters
    const techFilters = document.getElementById('tech-filters');
    const allTech = [...new Set(projects.flatMap(p => p.tech || []))].sort();
    
    let activeFilters = [];
    
    allTech.forEach(tech => {
        const btn = document.createElement('button');
        btn.className = 'filter-btn';
        btn.textContent = tech;
        btn.addEventListener('click', () => {
            btn.classList.toggle('active');
            if (btn.classList.contains('active')) {
                activeFilters.push(tech);
            } else {
                activeFilters = activeFilters.filter(t => t !== tech);
            }
            filterProjects(projects, activeFilters);
        });
        techFilters.appendChild(btn);
    });
    
    renderProjects(projects);
}

// Render projects
function renderProjects(projects) {
    const grid = document.getElementById('projects-grid');
    grid.innerHTML = projects.map((project, index) => `
        <div class="project-card" data-index="${index}" data-tech="${(project.tech || []).join(',')}">
            <img src="${project.image || project.cover}" alt="${project.title}" class="project-img">
            <div class="project-content">
                <h3>${project.title}</h3>
                <p>${truncate(project.description, 120)}</p>
                <div class="tech-tags">
                    ${(project.tech || []).map(t => `<span class="tech-tag">${t}</span>`).join('')}
                </div>
            </div>
        </div>
    `).join('');
    
    document.querySelectorAll('.project-card').forEach(card => {
        card.addEventListener('click', async () => {
            const index = card.dataset.index;
            await showProjectModal(index);
        });
    });
}

// Filter projects
function filterProjects(projects, activeFilters) {
    document.querySelectorAll('.project-card').forEach(card => {
        const cardTech = card.dataset.tech.split(',').filter(t => t);
        const shouldShow = activeFilters.length === 0 || 
                          activeFilters.every(filter => cardTech.includes(filter));
        card.style.display = shouldShow ? 'block' : 'none';
    });
}

// Show project modal
async function showProjectModal(index) {
    const data = await loadData();
    const project = data.projects[index];
    if (!project) return;
    
    const modal = document.getElementById('modal');
    const modalBody = document.getElementById('modal-body');
    
    let detailsHTML = '';
    
    if (project.details && project.details.includes('github.com') && project.details.includes('/blob/') && project.details.endsWith('.md')) {
        const rawUrl = project.details
            .replace('github.com', 'raw.githubusercontent.com')
            .replace('/blob/', '/');
        
        try {
            const response = await fetch(rawUrl);
            const markdown = await response.text();
            detailsHTML = marked.parse(markdown);
        } catch (error) {
            detailsHTML = `<p>Failed to load project details.</p>`;
        }
    } else if (project.details) {
        detailsHTML = project.details;
    } else {
        detailsHTML = `<p>${project.description}</p>`;
    }
    
    modalBody.innerHTML = `
        <img src="${project.cover || project.image}" alt="${project.title}" style="width: 100%; border-radius: 10px; margin-bottom: 2rem;">
        <h1>${project.title}</h1>
        <div class="tech-tags" style="margin: 1rem 0;">
            ${(project.tech || []).map(t => `<span class="tech-tag">${t}</span>`).join('')}
        </div>
        ${detailsHTML}
        ${project.source ? `<a href="${project.source}" target="_blank" class="btn btn-primary" style="margin-top: 2rem; display: inline-flex;"><i class="fab fa-github"></i> View Source Code</a>` : ''}
    `;
    
    modalBody.querySelectorAll('a').forEach(link => {
        if (link.href && !link.href.startsWith(window.location.origin)) {
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
        }
    });
    
    modal.classList.add('active');
}

// Initialize blog
async function initBlog() {
    const data = await loadData();
    const posts = data.blogPosts || [];
    
    const grid = document.getElementById('blog-grid');
    
    if (posts.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-pen-fancy"></i>
                <h3>No Blog Posts Yet</h3>
                <p>Stay tuned for upcoming articles and tutorials!</p>
            </div>
        `;
        const subtitle = document.querySelector('#blog .section-subtitle');
        if (subtitle) subtitle.style.display = 'none';
        return;
    }
    
    grid.innerHTML = posts.map((post, index) => `
        <div class="blog-card" data-index="${index}">
            <img src="${post.image || post.cover}" alt="${post.title}" class="blog-img">
            <div class="blog-content">
                <div class="blog-meta">
                    <span class="blog-category"><i class="fas fa-tag"></i> ${post.category}</span>
                    <span><i class="fas fa-calendar"></i> ${post.date}</span>
                    <span><i class="fas fa-clock"></i> ${post.readTime}</span>
                </div>
                <h3>${post.title}</h3>
                <p>${truncate(post.excerpt, 120)}</p>
            </div>
        </div>
    `).join('');
    
    document.querySelectorAll('.blog-card').forEach(card => {
        card.addEventListener('click', async () => {
            const index = card.dataset.index;
            await showBlogModal(index);
        });
    });
}

// Show blog modal
async function showBlogModal(index) {
    const data = await loadData();
    const post = data.blogPosts[index];
    if (!post) return;
    
    const modal = document.getElementById('modal');
    const modalBody = document.getElementById('modal-body');
    
    modalBody.innerHTML = `
        <img src="${post.cover || post.image}" alt="${post.title}" style="width: 100%; border-radius: 10px; margin-bottom: 2rem;">
        <div class="blog-meta" style="margin-bottom: 1rem;">
            <span class="blog-category"><i class="fas fa-tag"></i> ${post.category}</span>
            <span><i class="fas fa-calendar"></i> ${post.date}</span>
            <span><i class="fas fa-clock"></i> ${post.readTime}</span>
        </div>
        <h1>${post.title}</h1>
        <p style="font-size: 1.2rem; color: var(--text-muted); margin-bottom: 2rem;">${post.excerpt}</p>
        ${post.content}
    `;
    
    modal.classList.add('active');
}

// Initialize pricing
async function initPricing() {
    const inlinePricing = []; // your inline fallback plans
    let plans = inlinePricing;

    try {
        // Try remote first
        const resp = await fetch('https://yasserbdj96.pythonanywhere.com/pricing.json');
        if (resp.ok) {
            plans = await resp.json();
        } else {
            throw new Error('Remote pricing failed: ' + resp.status);
        }
    } catch (remoteErr) {
        console.warn('Remote pricing failed, trying local pricing.json', remoteErr);
        try {
            plans = await tryLocalJSON('./pricing.json', inlinePricing);
        } catch (localErr) {
            console.error('Local pricing also failed, using inline fallback', localErr);
            plans = inlinePricing;
        }
    }

    const grid = document.getElementById('pricing-grid');
    grid.innerHTML = plans.map(plan => `
        <div class="pricing-card ${plan.featured ? 'featured' : ''}">
            <h3>${plan.title}</h3>
            <div class="pricing-price">
                ${plan.price}
                ${plan.unit ? `<span>${plan.unit}</span>` : ''}
            </div>
            <ul class="pricing-features">
                ${plan.features.map(feature => {
                    const isUnavailable = feature.startsWith('×');
                    const cleanFeature = feature.replace(/^[×]\s*/, '');
                    return `<li class="${isUnavailable ? 'unavailable' : ''}">${cleanFeature}</li>`;
                }).join('')}
            </ul>
            <a href="#contact" class="btn btn-primary" onclick="fillContactForm('${plan.title}')">
                <i class="fas fa-check-circle"></i> ${plan.button}
            </a>
        </div>
    `).join('');
}


// Fill contact form
function fillContactForm(planTitle) {
    const messageField = document.querySelector('#contact-form textarea[name="message"]');
    if (messageField) {
        messageField.value = `I'm interested in the ${planTitle} plan. `;
    }
}

// Contact form submission
const contactForm = document.getElementById('contact-form');
if (contactForm) {
    contactForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const submitBtn = this.querySelector('button[type="submit"]');
        const originalHTML = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
        submitBtn.disabled = true;
        
        const formData = {
            name: this.name.value,
            email: this.email.value,
            message: this.message.value
        };
        
        try {
            const response = await fetch('https://yasserbdj96.pythonanywhere.com/api/contact', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
            
            const result = await response.json();
            if (result.success) {
                alert('✓ Message sent successfully! I will get back to you soon.');
                this.reset();
            } else {
                alert('Error: ' + (result.error || 'Failed to send message'));
            }
        } catch (error) {
            alert('Network error: ' + error.message);
        } finally {
            submitBtn.innerHTML = originalHTML;
            submitBtn.disabled = false;
        }
    });
}

// Modal close functionality
const modalClose = document.querySelector('.modal-close');
if (modalClose) {
    modalClose.addEventListener('click', () => {
        document.getElementById('modal').classList.remove('active');
    });
}

const modal = document.getElementById('modal');
if (modal) {
    modal.addEventListener('click', (e) => {
        if (e.target.id === 'modal') {
            modal.classList.remove('active');
        }
    });
}

// Close modal with Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        const modal = document.getElementById('modal');
        if (modal) {
            modal.classList.remove('active');
        }
    }
});

// Utility function to truncate text
function truncate(text, length) {
    if (!text) return '';
    return text.length > length ? text.substring(0, length) + '...' : text;
}

// Set current year in footer
const currentYearEl = document.getElementById('current-year');
if (currentYearEl) {
    currentYearEl.textContent = new Date().getFullYear();
}

// Fetch GitHub stats
async function fetchGitHubStats() {
    try {
        const response = await fetch('https://api.github.com/users/yasserbdj96');
        const data = await response.json();
        
        const statsContainer = document.getElementById('github-stats');
        if (statsContainer) {
            statsContainer.innerHTML = `
                <div class="stat-item">
                    <div class="stat-number">${data.public_repos}</div>
                    <div class="stat-label">Repositories</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">${data.followers}</div>
                    <div class="stat-label">Followers</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">${data.following}</div>
                    <div class="stat-label">Following</div>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error fetching GitHub stats:', error);
    }
}

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    initProjects();
    initBlog();
    initPricing();
    fetchGitHubStats();
});

// Add intersection observer for scroll animations
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// Observe all cards
window.addEventListener('load', () => {
    document.querySelectorAll('.project-card, .blog-card, .pricing-card').forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(card);
    });
});