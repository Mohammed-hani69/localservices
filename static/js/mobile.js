
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the mobile UI components
    initMobileUI();

    // Check if we're on a mobile device for redirection
    checkAndRedirectToMobile();

    // Check online status
    window.addEventListener('online', updateOnlineStatus);
    window.addEventListener('offline', updateOnlineStatus);
    updateOnlineStatus();

    // Handle service cards click with touch feedback
    const serviceCards = document.querySelectorAll('.service-card[data-href], .mobile-card[data-href]');
    serviceCards.forEach(card => {
        card.addEventListener('click', function() {
            const href = this.getAttribute('data-href');

            // Add touch feedback animation
            this.classList.add('card-pressed');

            // Navigate after animation completes
            if (href) {
                setTimeout(() => {
                    window.location.href = href;
                }, 150);
            }
        });

        // Remove animation class on touch end
        card.addEventListener('touchend', function() {
            setTimeout(() => {
                this.classList.remove('card-pressed');
            }, 150);
        });
    });

    // Initialize rating displays
    initRatingDisplays();

    // Handle tab switching with smooth transitions
    initTabSwitching();

    // Add smooth page transitions
    initPageTransitions();

    // Enable pull-to-refresh
    initPullToRefresh();
});

// Initialize mobile UI components
function initMobileUI() {
    // Initialize mobile tabs
    const mobileTabs = document.querySelectorAll('.mobile-tab');
    const mobileTabContents = document.querySelectorAll('.mobile-tab-content');

    mobileTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const target = this.getAttribute('data-target');

            // Update active state
            mobileTabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');

            // Show/hide content
            mobileTabContents.forEach(content => {
                if (content.id === target) {
                    content.style.display = 'block';
                } else {
                    content.style.display = 'none';
                }
            });
        });
    });

    // Initialize notification marking as read
    const notificationItems = document.querySelectorAll('.notification-item');

    notificationItems.forEach(item => {
        item.addEventListener('click', function() {
            if (this.classList.contains('unread')) {
                const notificationId = this.dataset.id;
                fetch(`/notifications/mark-read/${notificationId}`)
                    .then(response => {
                        if (response.ok) {
                            this.classList.remove('unread');
                        }
                    });
            }
        });
    });
}

// Initialize star rating displays
function initRatingDisplays() {
    const ratingDisplays = document.querySelectorAll('.rating-display');
    ratingDisplays.forEach(display => {
        const rating = parseFloat(display.getAttribute('data-rating')) || 0;
        let stars = '';
        for (let i = 1; i <= 5; i++) {
            if (i <= rating) {
                stars += '<i class="fas fa-star text-warning"></i>';
            } else if (i - 0.5 <= rating) {
                stars += '<i class="fas fa-star-half-alt text-warning"></i>';
            } else {
                stars += '<i class="far fa-star text-warning"></i>';
            }
        }
        display.innerHTML = stars;
    });
}

// Handle tab switching
function initTabSwitching() {
    const tabLinks = document.querySelectorAll('[data-tab]');

    tabLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();

            const tabId = this.getAttribute('data-tab');
            const tabContents = document.querySelectorAll('.tab-pane');

            // Update active state
            tabLinks.forEach(l => l.classList.remove('active'));
            this.classList.add('active');

            // Show/hide content
            tabContents.forEach(content => {
                if (content.id === tabId) {
                    content.classList.add('active', 'show');
                } else {
                    content.classList.remove('active', 'show');
                }
            });
        });
    });
}

// Add smooth page transitions
function initPageTransitions() {
    document.addEventListener('click', function(e) {
        // Check if the clicked element is a link to another page
        const link = e.target.closest('a');
        if (link && link.href && !link.getAttribute('target') && !link.getAttribute('data-bs-toggle')) {
            // Get current domain
            const currentDomain = window.location.hostname;
            const linkDomain = new URL(link.href).hostname;

            // Only apply transition for internal links
            if (currentDomain === linkDomain) {
                e.preventDefault();

                // Add transition effect
                document.body.classList.add('page-transition-out');

                // Navigate after transition
                setTimeout(() => {
                    window.location.href = link.href;
                }, 300);
            }
        }
    });

    // Add transition in class when page loads
    window.addEventListener('pageshow', function() {
        document.body.classList.remove('page-transition-out');
        document.body.classList.add('page-transition-in');

        setTimeout(() => {
            document.body.classList.remove('page-transition-in');
        }, 300);
    });
}

// Update online status indicator
function updateOnlineStatus() {
    const isOnline = navigator.onlineStatus !== undefined ? navigator.onlineStatus : navigator.onLine;

    if (!isOnline) {
        showMobileToast('أنت غير متصل بالإنترنت حاليًا', 'error');
    }
}

// Show mobile toast notifications
window.showMobileToast = function(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container');

    if (!toastContainer) {
        return;
    }

    const toast = document.createElement('div');
    toast.className = `toast align-items-center border-0 ${type === 'error' ? 'bg-danger' : type === 'success' ? 'bg-success' : 'bg-dark'}`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');

    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body text-white">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;

    toastContainer.appendChild(toast);

    const bsToast = new bootstrap.Toast(toast, {
        animation: true,
        autohide: true,
        delay: 3000
    });

    bsToast.show();

    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
};

// Check if device is mobile
window.isMobileDevice = function() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) || window.innerWidth < 768;
};

// Redirect to mobile version if needed
window.checkAndRedirectToMobile = function() {
    if (window.isMobileDevice()) {
        // Check if we're already on the mobile version
        if (!window.location.pathname.includes('/mobile/')) {
            const path = window.location.pathname;
            // Convert regular paths to mobile paths
            let mobilePath = path;

            // Map regular routes to mobile routes
            if (path === '/' || path === '/index') {
                mobilePath = '/mobile/';
            } else if (path.startsWith('/service/')) {
                const serviceId = path.split('/').pop();
                mobilePath = `/mobile/service/${serviceId}`;
            } else if (path === '/services') {
                mobilePath = '/mobile/services';
            } else if (path === '/dashboard') {
                mobilePath = '/mobile/dashboard';
            }

            // window.location.href = mobilePath + window.location.search;
        }
    } else {
        // Check if we're on the mobile version but using a desktop
        if (window.location.pathname.includes('/mobile/')) {
            // Convert mobile paths to regular paths
            const path = window.location.pathname;
            let desktopPath = path.replace('/mobile', '');

            if (desktopPath === '') {
                desktopPath = '/';
            }

            // window.location.href = desktopPath + window.location.search;
        }
    }
};

// Initialize rating displays based on data-rating attribute
function renderRatingStars(element, rating) {
    element.innerHTML = '';

    const fullStars = Math.floor(rating);
    const hasHalfStar = rating - fullStars >= 0.5;
    const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);

    // Add full stars
    for (let i = 0; i < fullStars; i++) {
        const star = document.createElement('i');
        star.className = 'fas fa-star text-warning';
        element.appendChild(star);
    }

    // Add half star if needed
    if (hasHalfStar) {
        const halfStar = document.createElement('i');
        halfStar.className = 'fas fa-star-half-alt text-warning';
        element.appendChild(halfStar);
    }

    // Add empty stars
    for (let i = 0; i < emptyStars; i++) {
        const emptyStar = document.createElement('i');
        emptyStar.className = 'far fa-star text-warning';
        element.appendChild(emptyStar);
    }
}

// Create toast container if it doesn't exist
if (!document.querySelector('.mobile-toast')) {
    const toastDiv = document.createElement('div');
    toastDiv.className = 'mobile-toast';
    document.body.appendChild(toastDiv);
}

// Create offline indicator if it doesn't exist
if (!document.querySelector('.mobile-offline-indicator')) {
    const offlineDiv = document.createElement('div');
    offlineDiv.className = 'mobile-offline-indicator';
    offlineDiv.textContent = 'أنت غير متصل بالإنترنت';
    document.body.appendChild(offlineDiv);
}

// Add smooth page transitions
function initPageTransitions() {
    // Add transition container if it doesn't exist
    if (!document.querySelector('.page-transition')) {
        const transitionDiv = document.createElement('div');
        transitionDiv.className = 'page-transition';
        document.body.appendChild(transitionDiv);
    }

    // Add CSS for page transitions
    const style = document.createElement('style');
    style.textContent = `
        .page-transition {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: #f7f7f7;
            z-index: 9999;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.3s ease;
        }
        .page-transition.active {
            opacity: 1;
            pointer-events: all;
        }
        .card-pressed {
            transform: scale(0.97);
            transition: transform 0.15s ease;
        }
    `;
    document.head.appendChild(style);


    // Intercept link clicks for smooth transitions
    document.querySelectorAll('a:not([target="_blank"])').forEach(link => {
        link.addEventListener('click', function(e) {
            // Skip if modifier keys are pressed
            if (e.ctrlKey || e.metaKey || e.shiftKey) return;

            const href = this.getAttribute('href');
            // Skip for hash links or javascript: links
            if (href && (href.startsWith('#') || href.startsWith('javascript:'))) return;

            e.preventDefault();

            // Show transition
            const transition = document.querySelector('.page-transition');
            transition.classList.add('active');

            // Navigate after transition
            setTimeout(() => {
                window.location.href = href;
            }, 300);
        });
    });
}

// Initialize pull-to-refresh functionality
function initPullToRefresh() {
    let touchStartY = 0;
    let touchEndY = 0;
    const minPullDistance = 150;

    // Create refresh indicator
    const refreshDiv = document.createElement('div');
    refreshDiv.className = 'pull-refresh-indicator';
    refreshDiv.innerHTML = '<i class="fas fa-sync-alt"></i>';
    document.body.appendChild(refreshDiv);

    // Add CSS for pull-to-refresh
    const style = document.createElement('style');
    style.textContent = `
        .pull-refresh-indicator {
            position: fixed;
            top: -60px;
            left: 50%;
            transform: translateX(-50%);
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background-color: var(--primary-color);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1001;
            transition: top 0.3s ease;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
        }
        .pull-refresh-indicator.visible {
            top: 65px;
        }
        .pull-refresh-indicator.refreshing i {
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    `;
    document.head.appendChild(style);

    // Only enable on main content areas
    if (document.querySelector('.main-content') || document.querySelector('.mobile-content')) {
        document.addEventListener('touchstart', function(e) {
            touchStartY = e.touches[0].clientY;
        }, false);

        document.addEventListener('touchmove', function(e) {
            if (document.scrollingElement.scrollTop === 0) {
                touchEndY = e.touches[0].clientY;
                const distance = touchEndY - touchStartY;

                if (distance > 50 && distance < minPullDistance) {
                    refreshDiv.style.top = (distance / 3) + 'px';
                }
            }
        }, false);

        document.addEventListener('touchend', function() {
            const distance = touchEndY - touchStartY;

            if (distance >= minPullDistance && document.scrollingElement.scrollTop === 0) {
                // Show refreshing animation
                refreshDiv.classList.add('visible', 'refreshing');

                // Reload page after animation
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                // Reset position
                refreshDiv.style.top = '-60px';
            }

            // Reset values
            touchStartY = 0;
            touchEndY = 0;
        }, false);
    }
}
