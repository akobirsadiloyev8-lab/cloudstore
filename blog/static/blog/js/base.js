// ============================================
// CLOUDSTORE - BASE JAVASCRIPT
// Modern Django Web Application
// ============================================

// ========== DARK MODE ==========
document.body.classList.add('dark-mode');

// ========== SIDEBAR FUNCTIONS ==========
function openSidebar() {
    document.getElementById('sidebar').classList.add('open');
    document.getElementById('sidebarOverlay').classList.add('show');
    document.body.style.overflow = 'hidden';
}

function closeSidebar() {
    document.getElementById('sidebar').classList.remove('open');
    document.getElementById('sidebarOverlay').classList.remove('show');
    document.body.style.overflow = '';
}

// ========== GLOBAL SEARCH ==========
function handleGlobalSearch(event) {
    if (event.key === 'Enter') {
        const query = document.getElementById('globalSearch').value.trim();
        if (query) {
            window.location.href = '/kitoblar/?q=' + encodeURIComponent(query);
        }
    }
}

// ========== UNREAD MESSAGES CHECK ==========
function checkUnreadMessages() {
    // This will be executed only if user is authenticated (check from template)
    fetch('/api/online-status/')
        .then(response => response.json())
        .then(data => {
            const badge = document.getElementById('sidebarUnreadBadge');
            if (badge && data.unread_count > 0) {
                badge.textContent = data.unread_count > 99 ? '99+' : data.unread_count;
                badge.style.display = 'inline-block';
            } else if (badge) {
                badge.style.display = 'none';
            }
        })
        .catch(err => console.log('Unread check error:', err));
}

// ========== TOUCH GESTURES ==========
let touchStartX = 0;
let touchEndX = 0;
const swipeThreshold = 80;

document.addEventListener('touchstart', e => {
    touchStartX = e.changedTouches[0].screenX;
}, { passive: true });

document.addEventListener('touchend', e => {
    touchEndX = e.changedTouches[0].screenX;
    handleSwipe();
}, { passive: true });

function handleSwipe() {
    const swipeDistance = touchEndX - touchStartX;
    const sidebar = document.getElementById('sidebar');
    if (swipeDistance > swipeThreshold && touchStartX < 50) {
        openSidebar();
    }
    if (swipeDistance < -swipeThreshold && sidebar.classList.contains('open')) {
        closeSidebar();
    }
}

// ========== KEYBOARD SHORTCUTS ==========
document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeSidebar();
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.getElementById('globalSearch');
        if (searchInput) searchInput.focus();
    }
});

// ========== PULL TO REFRESH ==========
let pullStartY = 0;
let pullMoveY = 0;
let isPulling = false;

document.addEventListener('touchstart', e => {
    if (window.scrollY === 0) {
        pullStartY = e.touches[0].clientY;
        isPulling = true;
    }
}, { passive: true });

document.addEventListener('touchmove', e => {
    if (!isPulling) return;
    pullMoveY = e.touches[0].clientY;
    const pullDistance = pullMoveY - pullStartY;
    if (pullDistance > 100 && window.scrollY === 0) {
        document.body.style.transform = `translateY(${Math.min(pullDistance * 0.3, 50)}px)`;
    }
}, { passive: true });

document.addEventListener('touchend', e => {
    if (!isPulling) return;
    const pullDistance = pullMoveY - pullStartY;
    if (pullDistance > 120 && window.scrollY === 0) {
        window.location.reload();
    }
    document.body.style.transform = '';
    isPulling = false;
}, { passive: true });

// ========== SERVICE WORKER ==========
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js', { scope: '/' })
        .then(() => console.log('SW registered'))
        .catch(err => console.log('SW error:', err));
}

// ========== TOAST FUNCTION ==========
window.showToast = function(message, duration = 3000) {
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();
    
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => toast.classList.add('show'), 10);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, duration);
};

// ========== INTERSECTION OBSERVER FOR ANIMATIONS ==========
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('card-animate');
            observer.unobserve(entry.target);
        }
    });
}, observerOptions);

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.book-card, .amz-book-card, .card').forEach(card => {
        observer.observe(card);
    });
});

// ========== IMAGE LAZY LOAD ANIMATION ==========
document.addEventListener('DOMContentLoaded', () => {
    const images = document.querySelectorAll('img');
    images.forEach(img => {
        if (img.complete) {
            img.classList.add('loaded');
        } else {
            img.addEventListener('load', () => img.classList.add('loaded'));
        }
    });
});

// ========== EXPORT FUNCTIONS ==========
window.cloudstore = {
    openSidebar,
    closeSidebar,
    handleGlobalSearch,
    checkUnreadMessages,
    showToast
};
