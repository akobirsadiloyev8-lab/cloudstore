// ============================================
// CLOUDSTORE - PWA FUNCTIONALITY
// Progressive Web App Installation & Features
// ============================================

let deferredPrompt;
const installBanner = document.getElementById('installBanner');
const sidebarInstallBtn = document.getElementById('sidebarInstallBtn');
const heroInstallBtn = document.getElementById('heroInstallBtn');

// ========== PWA INSTALL PROMPT ==========
window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    if (installBanner) installBanner.style.display = 'flex';
    if (sidebarInstallBtn) sidebarInstallBtn.style.display = 'flex';
    if (heroInstallBtn) heroInstallBtn.style.display = 'inline-flex';
});

// ========== INSTALL APP FUNCTION ==========
function installApp() {
    if (deferredPrompt) {
        deferredPrompt.prompt();
        deferredPrompt.userChoice.then((choiceResult) => {
            if (choiceResult.outcome === 'accepted') {
                hideInstallButtons();
            }
            deferredPrompt = null;
        });
    } else {
        showIOSInstallModal();
    }
}

// ========== iOS INSTALL MODAL ==========
function showIOSInstallModal() {
    if (window.navigator.standalone) return;
    let modal = document.getElementById('iosInstallModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'iosInstallModal';
        modal.innerHTML = `
            <div style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.8); z-index: 10000; display: flex; align-items: center; justify-content: center; padding: 20px;" onclick="this.parentElement.remove()">
                <div style="background: #191919; border-radius: 20px; padding: 30px; max-width: 340px; width: 100%; box-shadow: 0 20px 60px rgba(0,0,0,0.5);" onclick="event.stopPropagation()">
                    <div style="text-align: center; margin-bottom: 25px;">
                        <img src="/static/icons/icon-96x96.png" style="width: 70px; height: 70px; border-radius: 15px; margin-bottom: 15px;">
                        <h3 style="color: #fff; font-size: 1.3rem; margin-bottom: 5px;">Cloudstore ilovasini o'rnatish</h3>
                        <p style="color: #9ca3af; font-size: 0.9rem;">Tezkor kirish uchun bosh ekranga qo'shing</p>
                    </div>
                    <div style="background: rgba(255,255,255,0.05); border-radius: 15px; padding: 20px;">
                        <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 18px; padding-bottom: 18px; border-bottom: 1px solid rgba(255,255,255,0.1);">
                            <div style="width: 40px; height: 40px; background: #2e7400; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; color: #87e64b;">1</div>
                            <div style="flex: 1;">
                                <p style="color: #fff; font-weight: 600; margin-bottom: 3px;">Safari pastida</p>
                                <p style="color: #9ca3af; font-size: 0.85rem;">Share tugmasini bosing</p>
                            </div>
                        </div>
                        <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 18px; padding-bottom: 18px; border-bottom: 1px solid rgba(255,255,255,0.1);">
                            <div style="width: 40px; height: 40px; background: #2e7400; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; color: #87e64b;">2</div>
                            <div style="flex: 1;">
                                <p style="color: #fff; font-weight: 600; margin-bottom: 3px;">Pastga suring</p>
                                <p style="color: #9ca3af; font-size: 0.85rem;">Add to Home Screen</p>
                            </div>
                        </div>
                        <div style="display: flex; align-items: center; gap: 15px;">
                            <div style="width: 40px; height: 40px; background: linear-gradient(135deg, #22c55e, #16a34a); border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1.2rem;">✓</div>
                            <div style="flex: 1;">
                                <p style="color: #fff; font-weight: 600; margin-bottom: 3px;">Add tugmasini bosing</p>
                                <p style="color: #9ca3af; font-size: 0.85rem;">Ilova bosh ekranda paydo bo'ladi</p>
                            </div>
                        </div>
                    </div>
                    <button onclick="this.closest('#iosInstallModal').remove()" style="width: 100%; margin-top: 20px; padding: 14px; background: #87e64b; border: none; border-radius: 12px; color: #1a4200; font-weight: 600; font-size: 1rem; cursor: pointer;">Tushunarli</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }
}

// ========== HIDE INSTALL BUTTONS ==========
function hideInstallButtons() {
    if (installBanner) installBanner.style.display = 'none';
    if (sidebarInstallBtn) sidebarInstallBtn.style.display = 'none';
    if (heroInstallBtn) {
        heroInstallBtn.onclick = null;
        heroInstallBtn.style.background = 'linear-gradient(135deg, #22c55e, #16a34a)';
        heroInstallBtn.style.cursor = 'default';
        heroInstallBtn.innerHTML = '<i class="fas fa-check-circle"></i> O\'rnatilgan';
    }
    localStorage.setItem('appInstalled', 'true');
}

// ========== CLOSE INSTALL BANNER ==========
function closeInstallBanner() {
    if (installBanner) {
        installBanner.style.display = 'none';
        localStorage.setItem('installBannerClosed', Date.now());
    }
}

// ========== APP INSTALLED EVENT ==========
window.addEventListener('appinstalled', () => hideInstallButtons());

// ========== iOS DETECTION ==========
if (/iPhone|iPad|iPod/.test(navigator.userAgent) && !window.navigator.standalone) {
    if (sidebarInstallBtn) sidebarInstallBtn.style.display = 'flex';
    if (heroInstallBtn) heroInstallBtn.style.display = 'inline-flex';
}

// ========== CHECK IF ALREADY INSTALLED ==========
if (localStorage.getItem('appInstalled') === 'true' || window.matchMedia('(display-mode: standalone)').matches) {
    setTimeout(() => {
        const heroBtn = document.getElementById('heroInstallBtn');
        if (heroBtn) {
            heroBtn.onclick = null;
            heroBtn.style.background = 'linear-gradient(135deg, #22c55e, #16a34a)';
            heroBtn.style.cursor = 'default';
            heroBtn.innerHTML = '<i class="fas fa-check-circle"></i> O\'rnatilgan';
        }
    }, 100);
}

// ========== EXPORT FUNCTIONS ==========
window.pwa = {
    installApp,
    showIOSInstallModal,
    hideInstallButtons,
    closeInstallBanner
};

// Make functions globally available
window.installApp = installApp;
window.closeInstallBanner = closeInstallBanner;
