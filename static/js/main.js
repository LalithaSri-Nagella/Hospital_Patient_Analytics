/**
 * Hospital Patient Data Analysis System - Base JavaScript
 */

document.addEventListener('DOMContentLoaded', function () {
    // 1. Mobile Sidebar Toggle
    const sidebarToggleBtn = document.getElementById('sidebarToggleBtn');
    const sidebarCloseBtn = document.getElementById('sidebarCloseBtn');
    const appSidebar = document.getElementById('appSidebar');

    if (sidebarToggleBtn && appSidebar) {
        sidebarToggleBtn.addEventListener('click', function () {
            appSidebar.classList.toggle('show');
        });
    }

    if (sidebarCloseBtn && appSidebar) {
        sidebarCloseBtn.addEventListener('click', function () {
            appSidebar.classList.remove('show');
        });
    }

    // Close sidebar on click outside on mobile
    document.addEventListener('click', function (event) {
        if (window.innerWidth < 992 && appSidebar && appSidebar.classList.contains('show')) {
            if (!appSidebar.contains(event.target) && !sidebarToggleBtn.contains(event.target)) {
                appSidebar.classList.remove('show');
            }
        }
    });

    // 2. Auto-dismiss alerts after 6 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 6000);
    });

    // 3. Confirm Delete Prompts
    const deleteButtons = document.querySelectorAll('[data-confirm-delete]');
    deleteButtons.forEach(function (btn) {
        btn.addEventListener('click', function (e) {
            const message = btn.getAttribute('data-confirm-delete') || 'Are you sure you want to delete this record?';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });
});
