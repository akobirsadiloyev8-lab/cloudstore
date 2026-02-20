// ============================================
// CLOUDSTORE - PAGE TRANSITIONS
// Smooth page navigation and loading effects
// ============================================

(function() {
    'use strict';
    
    // ========== CREATE OVERLAY AND SPINNER ==========
    const overlay = document.createElement('div');
    overlay.className = 'page-transition-overlay';
    document.body.appendChild(overlay);
    
    const spinner = document.createElement('div');
    spinner.className = 'page-spinner';
    spinner.innerHTML = '<div class="spinner"></div>';
    document.body.appendChild(spinner);
    
    // ========== PAGE ENTER ANIMATION ==========
    function animatePageEnter() {
        const content = document.querySelector('.main-content, main, .content, .app-container');
        if (content) {
            content.style.opacity = '0';
            content.style.transform = 'translateY(30px)';
            
            requestAnimationFrame(() => {
                content.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
                content.style.opacity = '1';
                content.style.transform = 'translateY(0)';
            });
        }
    }
    
    // ========== PAGE EXIT ANIMATION ==========
    function animatePageExit(callback) {
        const content = document.querySelector('.main-content, main, .content, .app-container');
        const loader = document.getElementById('page-loader');
        const progress = loader ? loader.querySelector('.progress') : null;
        
        // Start progress bar
        if (progress) {
            progress.style.width = '30%';
        }
        
        // Show spinner
        spinner.classList.add('visible');
        
        if (content) {
            content.style.transition = 'opacity 0.3s ease, transform 0.3s ease, filter 0.3s ease';
            content.style.opacity = '0.3';
            content.style.transform = 'translateY(-10px) scale(0.99)';
            content.style.filter = 'blur(3px)';
        }
        
        // Callback after transition
        setTimeout(callback, 300);
    }
    
    // ========== HANDLE LINK CLICKS ==========
    document.addEventListener('click', function(e) {
        const link = e.target.closest('a');
        
        // Link validation
        if (!link) return;
        if (link.target === '_blank') return;
        if (link.href.includes('#')) return;
        if (link.href.includes('javascript:')) return;
        if (link.href.includes('mailto:')) return;
        if (link.href.includes('tel:')) return;
        if (link.getAttribute('download')) return;
        if (e.ctrlKey || e.metaKey || e.shiftKey) return;
        
        // Only internal links
        const url = new URL(link.href);
        if (url.origin !== window.location.origin) return;
        
        // Prevent default and animate
        e.preventDefault();
        
        animatePageExit(() => {
            window.location.href = link.href;
        });
    });
    
    // ========== BACK BUTTON ==========
    window.addEventListener('popstate', function() {
        animatePageExit(() => {
            // Browser will handle navigation
        });
    });
    
    // ========== PAGE LOADED ==========
    window.addEventListener('load', function() {
        // Hide spinner
        spinner.classList.remove('visible');
        
        // Hide overlay
        overlay.classList.remove('active');
        
        // Reset content
        const content = document.querySelector('.main-content, main, .content, .app-container');
        if (content) {
            content.style.opacity = '';
            content.style.transform = '';
            content.style.filter = '';
        }
    });
    
    // ========== PAGESHOW (BACK/FORWARD CACHE) ==========
    window.addEventListener('pageshow', function(e) {
        if (e.persisted) {
            // Page restored from cache
            spinner.classList.remove('visible');
            overlay.classList.remove('active');
            
            const content = document.querySelector('.main-content, main, .content, .app-container');
            if (content) {
                content.style.opacity = '1';
                content.style.transform = 'translateY(0)';
                content.style.filter = 'none';
            }
            
            // Reset progress bar
            const progress = document.querySelector('#page-loader .progress');
            if (progress) {
                progress.style.width = '0%';
            }
        }
    });
    
})();
