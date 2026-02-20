// ============================================
// CLOUDSTORE - LOADING PROGRESS BAR
// Enhanced page loading experience
// ============================================

(function() {
    'use strict';
    
    const loader = document.getElementById('page-loader');
    const progress = loader ? loader.querySelector('.progress') : null;
    
    if (!loader || !progress) return;
    
    let width = 0;
    
    // ========== START LOADING ==========
    function startLoading() {
        width = 0;
        const interval = setInterval(() => {
            if (width < 90) {
                width += Math.random() * 10;
                progress.style.width = Math.min(width, 90) + '%';
            }
        }, 100);
        
        window.addEventListener('load', () => {
            clearInterval(interval);
            progress.style.width = '100%';
            setTimeout(() => {
                progress.style.opacity = '0';
                setTimeout(() => {
                    progress.style.width = '0%';
                    progress.style.opacity = '1';
                }, 300);
            }, 200);
        });
    }
    
    // Start loading immediately
    startLoading();
    
    // ========== AJAX/FETCH REQUESTS ==========
    document.addEventListener('click', (e) => {
        const link = e.target.closest('a[href]');
        if (link && !link.href.includes('#') && !link.target && !e.ctrlKey && !e.metaKey) {
            progress.style.width = '30%';
        }
    });
    
})();
