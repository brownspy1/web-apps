/* ==========================================================================
   Exam Seat Plan Management System - Interactive UX Helpers
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  // Auto-dismiss toasts after 5 seconds
  const toasts = document.querySelectorAll('.toast');
  toasts.forEach(toast => {
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 5000);
  });

  // Mobile menu toggle
  const menuBtn = document.querySelector('.mobile-menu-btn');
  const navMenu = document.querySelector('.nav-menu');
  if (menuBtn && navMenu) {
    menuBtn.addEventListener('click', () => {
      navMenu.classList.toggle('open');
    });
  }

  // Close modals on escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      const openModals = document.querySelectorAll('.modal-overlay[style*="display: flex"], .modal-overlay[style*="display:flex"], .modal[style*="display: flex"], .modal[style*="display:flex"]');
      openModals.forEach(m => m.style.display = 'none');
    }
  });
});

function dismissToast(btn) {
  const toast = btn.closest('.toast');
  if (toast) {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.25s ease';
    setTimeout(() => toast.remove(), 250);
  }
}
