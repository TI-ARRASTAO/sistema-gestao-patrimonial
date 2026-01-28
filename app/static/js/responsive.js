/**
 * Sistema de Gestão Patrimonial - Funcionalidades Responsivas
 */

class ResponsiveManager {
    constructor() {
        this.init();
        this.setupEventListeners();
        this.setupAccessibility();
    }

    init() {
        this.isMobile = window.innerWidth <= 768;
        this.isTablet = window.innerWidth > 768 && window.innerWidth <= 1024;
        this.isDesktop = window.innerWidth > 1024;
        this.hasTouch = 'ontouchstart' in window;
        this.hasHover = window.matchMedia('(hover: hover)').matches;
        
        this.setupDynamicViewport();
        this.applyDeviceClasses();
    }

    setupEventListeners() {
        window.addEventListener('resize', this.debounce(() => {
            this.handleResize();
        }, 250));

        window.addEventListener('orientationchange', () => {
            setTimeout(() => this.handleOrientationChange(), 100);
        });

        document.addEventListener('keydown', (e) => {
            this.handleKeyboardNavigation(e);
        });

        if (this.hasTouch) {
            this.setupTouchGestures();
        }
    }

    setupAccessibility() {
        const handleKeydown = (e) => {
            if (e.key === 'Tab') {
                document.body.classList.add('keyboard-navigation');
            }
        };
        
        const handleMousedown = () => {
            document.body.classList.remove('keyboard-navigation');
        };
        
        document.addEventListener('keydown', handleKeydown, { passive: true });
        document.addEventListener('mousedown', handleMousedown, { passive: true });

        this.setupScreenReaderAnnouncements();
    }

    handleResize() {
        const newWidth = window.innerWidth;
        const oldIsMobile = this.isMobile;
        
        this.isMobile = newWidth <= 768;
        this.isTablet = newWidth > 768 && newWidth <= 1024;
        this.isDesktop = newWidth > 1024;

        if (oldIsMobile !== this.isMobile) {
            this.handleBreakpointChange();
        }

        this.applyDeviceClasses();
    }

    handleOrientationChange() {
        if (this.isMobile) {
            this.setupDynamicViewport();
        }
    }

    handleBreakpointChange() {
        if (this.isDesktop) {
            const sidebar = document.getElementById('sidebar');
            const overlay = document.getElementById('overlay');
            
            if (sidebar) sidebar.classList.remove('open');
            if (overlay) overlay.classList.remove('active');
        }
    }

    setupDynamicViewport() {
        if (this.vhResizeHandler) {
            window.removeEventListener('resize', this.vhResizeHandler);
        }
        
        this.vhResizeHandler = () => {
            const vh = window.innerHeight * 0.01;
            document.documentElement.style.setProperty('--vh', `${vh}px`);
        };

        this.vhResizeHandler();
        window.addEventListener('resize', this.vhResizeHandler);
    }

    applyDeviceClasses() {
        const body = document.body;
        body.classList.remove('is-mobile', 'is-tablet', 'is-desktop', 'has-touch', 'has-hover');
        
        if (this.isMobile) body.classList.add('is-mobile');
        if (this.isTablet) body.classList.add('is-tablet');
        if (this.isDesktop) body.classList.add('is-desktop');
        if (this.hasTouch) body.classList.add('has-touch');
        if (this.hasHover) body.classList.add('has-hover');
    }

    setupTouchGestures() {
        let startX, startY, startTime;

        document.addEventListener('touchstart', (e) => {
            const touch = e.touches[0];
            startX = touch.clientX;
            startY = touch.clientY;
            startTime = Date.now();
        }, { passive: true });

        document.addEventListener('touchend', (e) => {
            if (!startX || !startY) return;

            const touch = e.changedTouches[0];
            const endX = touch.clientX;
            const endY = touch.clientY;
            const endTime = Date.now();

            const deltaX = endX - startX;
            const deltaY = endY - startY;
            const deltaTime = endTime - startTime;

            if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 50 && deltaTime < 300) {
                if (deltaX > 0) {
                    this.handleSwipeRight();
                } else {
                    this.handleSwipeLeft();
                }
            }

            startX = startY = null;
        }, { passive: true });
    }

    handleSwipeRight() {
        if (!this.isMobile) return;
        
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('overlay');
        
        if (sidebar && !sidebar.classList.contains('open')) {
            sidebar.classList.add('open');
            if (overlay) overlay.classList.add('active');
        }
    }

    handleSwipeLeft() {
        if (!this.isMobile) return;
        
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('overlay');
        
        if (sidebar && sidebar.classList.contains('open')) {
            sidebar.classList.remove('open');
            if (overlay) overlay.classList.remove('active');
        }
    }

    handleKeyboardNavigation(e) {
        if (e.key === 'Escape') {
            this.closeAllModals();
            this.closeAllDropdowns();
        } else if (e.key === 'Enter' && e.target.matches('[role="button"]')) {
            e.target.click();
        }
    }

    setupScreenReaderAnnouncements() {
        const announcer = document.createElement('div');
        announcer.setAttribute('aria-live', 'polite');
        announcer.setAttribute('aria-atomic', 'true');
        announcer.className = 'sr-only';
        announcer.id = 'screen-reader-announcer';
        document.body.appendChild(announcer);

        window.announceToScreenReader = (message) => {
            announcer.textContent = message;
            setTimeout(() => {
                announcer.textContent = '';
            }, 1000);
        };
    }

    closeAllModals() {
        const modals = document.querySelectorAll('.modal, [id$="-modal"]');
        modals.forEach(modal => {
            modal.classList.add('hidden');
        });
    }

    closeAllDropdowns() {
        const dropdowns = document.querySelectorAll('.dropdown-menu');
        dropdowns.forEach(dropdown => {
            dropdown.classList.add('hidden');
        });
    }

    debounce(func, wait) {
        let timeout;
        return function(...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }

    showResponsiveNotification(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        const baseClasses = 'fixed z-50 p-4 rounded-lg shadow-lg text-white fade-in';
        const typeClasses = {
            success: 'bg-green-500',
            error: 'bg-red-500',
            warning: 'bg-yellow-500',
            info: 'bg-blue-500'
        };

        const positionClasses = this.isMobile 
            ? 'top-4 left-4 right-4' 
            : 'top-4 right-4 max-w-sm';

        notification.className = `${baseClasses} ${typeClasses[type]} ${positionClasses}`;
        
        const container = document.createElement('div');
        container.className = 'flex items-center justify-between';
        
        const messageSpan = document.createElement('span');
        messageSpan.className = 'flex-1 mr-3';
        messageSpan.textContent = message;
        
        const closeButton = document.createElement('button');
        closeButton.className = 'text-white hover:text-gray-200 flex-shrink-0';
        closeButton.onclick = () => notification.remove();
        closeButton.innerHTML = `
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
        `;
        
        container.appendChild(messageSpan);
        container.appendChild(closeButton);
        notification.appendChild(container);

        document.body.appendChild(notification);

        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, duration);

        if (window.announceToScreenReader) {
            window.announceToScreenReader(message);
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.responsiveManager = new ResponsiveManager();
    
    window.showNotification = (message, type, duration) => {
        window.responsiveManager.showResponsiveNotification(message, type, duration);
    };
});