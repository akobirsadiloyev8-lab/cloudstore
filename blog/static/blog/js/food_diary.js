function getCSRF() {
    return document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='))?.split('=')[1] || '';
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = 'toast ' + type + ' show';
    setTimeout(() => toast.classList.remove('show'), 3000);
}

async function deleteIntake(id) {
    if (!confirm("O'chirmoqchimisiz?")) return;
    
    try {
        const res = await fetch(`/api/food-intake/${id}/delete/`, {
            method: 'POST',
            headers: { 'X-CSRFToken': getCSRF() }
        });
        
        const data = await res.json();
        if (data.success) {
            showToast("O'chirildi!", "success");
            setTimeout(() => location.reload(), 500);
        } else {
            showToast(data.error || 'Xatolik', 'error');
        }
    } catch (err) {
        showToast('Server xatosi', 'error');
    }
}

// Animate calories ring
document.addEventListener('DOMContentLoaded', function() {
    const ring = document.getElementById('caloriesRing');
    if (ring) {
        const circumference = 2 * Math.PI * 75;
        const progress = parseFloat(ring.dataset.progress || 0);
        const offset = circumference - (progress / 100) * circumference;
        setTimeout(() => {
            ring.style.strokeDashoffset = offset;
        }, 100);
    }
});
