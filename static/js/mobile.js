document.addEventListener('DOMContentLoaded', function() {
    // Initialize the mobile UI components
    initMobileUI();
    
    // Check online status
    window.addEventListener('online', updateOnlineStatus);
    window.addEventListener('offline', updateOnlineStatus);
    updateOnlineStatus();
    
    // Handle service cards click
    const serviceCards = document.querySelectorAll('.mobile-card[data-href]');
    serviceCards.forEach(card => {
        card.addEventListener('click', function() {
            const href = this.getAttribute('data-href');
            if (href) {
                window.location.href = href;
            }
        });
    });
    
    // Initialize rating displays
    initRatingDisplays();
    
    // Handle tab switching
    initTabSwitching();
});

// Initialize mobile UI components
function initMobileUI() {
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
}

// Update online status indicator
function updateOnlineStatus() {
    const offlineIndicator = document.querySelector('.mobile-offline-indicator');
    if (offlineIndicator) {
        if (navigator.onLine) {
            offlineIndicator.style.display = 'none';
        } else {
            offlineIndicator.style.display = 'block';
        }
    }
}

// Display toast notification
window.showMobileToast = function(message, type = 'info') {
    const toast = document.querySelector('.mobile-toast');
    if (toast) {
        // Clear any existing classes except 'mobile-toast'
        toast.className = 'mobile-toast';
        
        // Add appropriate class based on type
        if (type === 'success' || type === 'error') {
            toast.classList.add(type);
        }
        
        toast.textContent = message;
        toast.classList.add('show');
        
        // Hide toast after 3 seconds
        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }
};

// Initialize rating displays based on data-rating attribute
function initRatingDisplays() {
    const ratingElements = document.querySelectorAll('.rating-display');
    ratingElements.forEach(element => {
        const rating = parseFloat(element.getAttribute('data-rating')) || 0;
        renderRatingStars(element, rating);
    });
}

// Render star rating
function renderRatingStars(element, rating) {
    element.innerHTML = '';
    
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating - fullStars >= 0.5;
    const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);
    
    // Add full stars
    for (let i = 0; i < fullStars; i++) {
        const star = document.createElement('i');
        star.className = 'fas fa-star';
        element.appendChild(star);
    }
    
    // Add half star if needed
    if (hasHalfStar) {
        const halfStar = document.createElement('i');
        halfStar.className = 'fas fa-star-half-alt';
        element.appendChild(halfStar);
    }
    
    // Add empty stars
    for (let i = 0; i < emptyStars; i++) {
        const emptyStar = document.createElement('i');
        emptyStar.className = 'far fa-star';
        element.appendChild(emptyStar);
    }
}

// Initialize tab switching functionality
function initTabSwitching() {
    const tabs = document.querySelectorAll('.mobile-tab[data-target]');
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const target = this.getAttribute('data-target');
            
            // Hide all tab contents
            document.querySelectorAll('.mobile-tab-content').forEach(content => {
                content.style.display = 'none';
            });
            
            // Show the selected tab content
            const targetContent = document.getElementById(target);
            if (targetContent) {
                targetContent.style.display = 'block';
            }
            
            // Update active tab
            document.querySelectorAll('.mobile-tab').forEach(t => {
                t.classList.remove('active');
            });
            this.classList.add('active');
        });
    });
}

// Show loading spinner
window.showMobileSpinner = function() {
    if (!document.querySelector('.mobile-spinner')) {
        const spinner = document.createElement('div');
        spinner.className = 'mobile-spinner';
        spinner.innerHTML = '<div class="mobile-spinner-inner"></div>';
        document.body.appendChild(spinner);
    }
};

// Hide loading spinner
window.hideMobileSpinner = function() {
    const spinner = document.querySelector('.mobile-spinner');
    if (spinner) {
        spinner.remove();
    }
};

// Function to detect if device is mobile
window.isMobileDevice = function() {
    return (window.innerWidth <= 768);
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
            
            window.location.href = mobilePath + window.location.search;
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
            
            window.location.href = desktopPath + window.location.search;
        }
    }
};

// Call redirect check (optional - enable if you want automatic redirection)
// window.checkAndRedirectToMobile();