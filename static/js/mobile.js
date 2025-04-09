document.addEventListener('DOMContentLoaded', function() {
    // تهيئة مكونات واجهة المستخدم
    initMobileUI();

    // التحقق من نوع الجهاز للتوجيه
    checkAndRedirectToMobile();

    // التحقق من حالة الاتصال
    window.addEventListener('online', updateOnlineStatus);
    window.addEventListener('offline', updateOnlineStatus);
    updateOnlineStatus();

    // إضافة الإيموشن إلى العناصر
    addEmojisToElements();

    // معالجة النقر على بطاقات الخدمات مع تأثير اللمس
    initCardTouchFeedback();

    // تهيئة عرض التقييمات
    initRatingDisplays();

    // معالجة تبديل التبويبات مع انتقالات سلسة
    initTabSwitching();

    // إضافة انتقالات سلسة بين الصفحات
    initPageTransitions();

    // تمكين ميزة السحب للتحديث
    initPullToRefresh();

    // تفعيل التمرير السلس
    initSmoothScrolling();

    // تفعيل مبدّل الوضع المظلم
    initThemeToggle();

    // تفعيل تأثيرات الرسوم المتحركة
    initAnimations();

    // تهيئة البنرات المتحركة
    initBannerSlider();
});

// تهيئة مكونات واجهة المستخدم للأجهزة المحمولة
function initMobileUI() {
    // تهيئة التبويبات
    const mobileTabs = document.querySelectorAll('.mobile-tab');
    const mobileTabContents = document.querySelectorAll('.mobile-tab-content');

    mobileTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const target = this.getAttribute('data-target');

            // تحديث حالة التنشيط
            mobileTabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');

            // إظهار/إخفاء المحتوى
            mobileTabContents.forEach(content => {
                if (content.id === target) {
                    content.style.display = 'block';
                    // إضافة تأثير الرسوم المتحركة للمحتوى المظهر
                    content.classList.add('fade-in');
                    setTimeout(() => {
                        content.classList.remove('fade-in');
                    }, 300);
                } else {
                    content.style.display = 'none';
                }
            });
        });
    });

    // تهيئة وضع العناصر غير المقروءة كمقروءة
    const notificationItems = document.querySelectorAll('.notification-item');

    notificationItems.forEach(item => {
        item.addEventListener('click', function() {
            if (this.classList.contains('unread')) {
                const notificationId = this.dataset.id;
                fetch(`/notifications/mark-read/${notificationId}`)
                    .then(response => {
                        if (response.ok) {
                            this.classList.remove('unread');
                            // إضافة تأثير انتقالي عند التحديث
                            this.style.transition = 'background-color 0.5s ease';

                            // تحديث إحصائيات الإشعارات
                            updateNotificationCount();
                        }
                    });
            }
        });
    });

    // إضافة تأثيرات التفاعل للأزرار
    const buttons = document.querySelectorAll('.btn, .action-button, .back-button');
    buttons.forEach(button => {
        button.addEventListener('mousedown', function() {
            this.style.transform = 'scale(0.97)';
        });
        button.addEventListener('mouseup', function() {
            this.style.transform = 'scale(1)';
        });
        button.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
        });
    });

    // تفعيل تحميل الصور بشكل تدريجي
    initLazyLoading();
}

// إضافة الإيموشن إلى عناصر الواجهة
function addEmojisToElements() {
    // قائمة بالعناصر التي تحتاج إيموشن مع الإيموشن المقابل
    const emojiMappings = [
        { selector: '.mobile-navbar a:nth-child(1) i', emoji: '🏠', title: 'الرئيسية' },
        { selector: '.mobile-navbar a:nth-child(2) i', emoji: '🛠️', title: 'الخدمات' },
        { selector: '.mobile-navbar a:nth-child(3) i', emoji: '🔔', title: 'الإشعارات' },
        { selector: '.mobile-navbar a:nth-child(4) i', emoji: '👤', title: 'حسابي' },
        { selector: '.empty-state-icon', emoji: '📭', replace: false },
        { selector: '.service-category:contains("صيانة")', emoji: '🔧', appendToStart: true },
        { selector: '.service-category:contains("تنظيف")', emoji: '🧹', appendToStart: true },
        { selector: '.service-category:contains("صحة")', emoji: '⚕️', appendToStart: true },
        { selector: '.service-category:contains("تعليم")', emoji: '📚', appendToStart: true },
        { selector: '.service-category:contains("طعام")', emoji: '🍽️', appendToStart: true },
        { selector: '.user-profile-summary h4', emoji: '👋', appendToEnd: true },
        { selector: '.booking-title', emoji: '📅', appendToStart: true }
    ];

    // البحث عن كل العناصر وإضافة الإيموشن
    emojiMappings.forEach(mapping => {
        const elements = document.querySelectorAll(mapping.selector);
        elements.forEach(element => {
            if (mapping.replace) {
                element.innerHTML = `<span class="emoji">${mapping.emoji}</span>`;
            } else if (mapping.appendToStart) {
                element.innerHTML = `<span class="emoji">${mapping.emoji}</span> ${element.innerHTML}`;
            } else if (mapping.appendToEnd) {
                element.innerHTML = `${element.innerHTML} <span class="emoji">${mapping.emoji}</span>`;
            } else {
                // إضافة إيموشن بجانب الأيقونة
                const parentElement = element.parentElement;
                if (parentElement && parentElement.classList.contains('nav-icon')) {
                    const titleElement = parentElement.nextElementSibling;
                    if (titleElement && titleElement.textContent === mapping.title) {
                        // إخفاء أيقونة Font Awesome واستبدالها بإيموشن
                        element.style.display = 'none';
                        parentElement.innerHTML += `<span class="emoji">${mapping.emoji}</span>`;
                    }
                }
            }
        });
    });

    // تخصيص الصفحات بعناوين تحتوي على إيموشن
    customizePageTitles();
}

// تخصيص عناوين الصفحات بإيموشن
function customizePageTitles() {
    // قائمة بالصفحات وعناوينها المخصصة
    const pageTitles = [
        { endpoint: 'mobile_index', title: 'الرئيسية', emoji: '🏠' },
        { endpoint: 'mobile_services', title: 'استكشف الخدمات', emoji: '🔍' },
        { endpoint: 'mobile_dashboard', title: 'ملفي الشخصي', emoji: '👤' },
        { endpoint: 'mobile_notifications', title: 'الإشعارات', emoji: '🔔' },
        { endpoint: 'mobile_service_details', title: 'تفاصيل الخدمة', emoji: '📋' },
        { endpoint: 'mobile_booking', title: 'حجز خدمة', emoji: '📅' },
        { endpoint: 'edit_user_profile', title: 'تعديل الملف الشخصي', emoji: '✏️' }
    ];

    // البحث عن العنوان الحالي
    const currentPath = window.location.pathname;
    const titleElement = document.querySelector('.mobile-title');

    if (titleElement) {
        // مطابقة الصفحة الحالية مع العناوين المعرفة
        for (const pageTitle of pageTitles) {
            if (
                (currentPath.includes(pageTitle.endpoint.replace('_', '/')) || 
                document.body.classList.contains(pageTitle.endpoint))
            ) {
                titleElement.innerHTML = `<span class="emoji">${pageTitle.emoji}</span> ${pageTitle.title}`;
                break;
            }
        }
    }
}

// تفعيل تأثير اللمس على البطاقات
function initCardTouchFeedback() {
    const touchableElements = document.querySelectorAll('.service-card[data-href], .mobile-card[data-href], .booking-card, .notification-item, .settings-item, .category-item[data-category]');

    touchableElements.forEach(element => {
        element.addEventListener('touchstart', function() {
            this.classList.add('card-pressed');
        }, { passive: true });

        element.addEventListener('touchend', function() {
            setTimeout(() => {
                this.classList.remove('card-pressed');
            }, 150);

            // التنقل إلى الصفحة المعنية إذا كان هناك رابط
            const href = this.getAttribute('data-href');
            const category = this.getAttribute('data-category');

            if (href) {
                setTimeout(() => {
                    window.location.href = href;
                }, 200);
            } else if (category) {
                // عند النقر على فئة، توجيه المستخدم إلى صفحة البحث مع تحديد الفئة
                setTimeout(() => {
                    window.location.href = `/mobile/services?category=${encodeURIComponent(category)}`;
                }, 200);
            }
        }, { passive: true });

        element.addEventListener('touchcancel', function() {
            this.classList.remove('card-pressed');
        }, { passive: true });

        // إضافة أيضًا لأجهزة الكمبيوتر
        element.addEventListener('click', function() {
            const href = this.getAttribute('data-href');
            const category = this.getAttribute('data-category');

            if (href) {
                window.location.href = href;
            } else if (category) {
                window.location.href = `/mobile/services?category=${encodeURIComponent(category)}`;
            }
        });
    });
}

// تهيئة عرض التقييمات
function initRatingDisplays() {
    const ratingDisplays = document.querySelectorAll('.rating-display');
    ratingDisplays.forEach(display => {
        const rating = parseFloat(display.getAttribute('data-rating')) || 0;
        renderRatingStars(display, rating);
    });
}

// عرض التقييمات بالنجوم
function renderRatingStars(element, rating) {
    element.innerHTML = '';

    const fullStars = Math.floor(rating);
    const hasHalfStar = rating - fullStars >= 0.5;
    const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);

    // إضافة النجوم الكاملة
    for (let i = 0; i < fullStars; i++) {
        const star = document.createElement('i');
        star.className = 'fas fa-star text-warning';
        element.appendChild(star);
    }

    // إضافة نصف نجمة إذا لزم الأمر
    if (hasHalfStar) {
        const halfStar = document.createElement('i');
        halfStar.className = 'fas fa-star-half-alt text-warning';
        element.appendChild(halfStar);
    }

    // إضافة النجوم الفارغة
    for (let i = 0; i < emptyStars; i++) {
        const emptyStar = document.createElement('i');
        emptyStar.className = 'far fa-star text-warning';
        element.appendChild(emptyStar);
    }
}

// معالجة تبديل التبويبات
function initTabSwitching() {
    const tabLinks = document.querySelectorAll('[data-tab]');

    tabLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();

            const tabId = this.getAttribute('data-tab');
            const tabContents = document.querySelectorAll('.tab-pane');

            // تحديث حالة التنشيط
            tabLinks.forEach(l => l.classList.remove('active'));
            this.classList.add('active');

            // إظهار/إخفاء المحتوى مع تأثير انتقالي
            tabContents.forEach(content => {
                if (content.id === tabId) {
                    content.style.display = 'block';
                    content.classList.add('fade-in');
                    setTimeout(() => {
                        content.classList.add('active', 'show');
                        content.classList.remove('fade-in');
                    }, 50);
                } else {
                    content.classList.remove('active', 'show');
                    setTimeout(() => {
                        content.style.display = 'none';
                    }, 300);
                }
            });
        });
    });
}

// إضافة انتقالات سلسة بين الصفحات
function initPageTransitions() {
    // إضافة حاوية التأثير الانتقالي إذا لم تكن موجودة
    if (!document.querySelector('.page-transition')) {
        const transitionDiv = document.createElement('div');
        transitionDiv.className = 'page-transition';
        document.body.appendChild(transitionDiv);
    }

    // إضافة CSS للتأثيرات الانتقالية
    const style = document.createElement('style');
    style.textContent = `
        .page-transition {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: var(--background-color);
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
            transform: scale(0.98);
            transition: transform 0.15s ease;
        }
    `;
    document.head.appendChild(style);

    // التقاط النقرات على الروابط للانتقالات السلسة
    document.querySelectorAll('a:not([target="_blank"])').forEach(link => {
        link.addEventListener('click', function(e) {
            // تخطي إذا تم الضغط على مفاتيح التعديل
            if (e.ctrlKey || e.metaKey || e.shiftKey) return;

            const href = this.getAttribute('href');
            // تخطي الروابط الداخلية أو روابط جافا سكريبت
            if (!href || href === '#' || href.startsWith('javascript:') || href.startsWith('#')) return;

            e.preventDefault();

            // إظهار تأثير الانتقال
            const transition = document.querySelector('.page-transition');
            transition.classList.add('active');

            // الانتقال بعد انتهاء التأثير
            setTimeout(() => {
                window.location.href = href;
            }, 300);
        });
    });
}

// تهيئة ميزة السحب للتحديث
function initPullToRefresh() {
    let touchStartY = 0;
    let touchEndY = 0;
    const minPullDistance = 150;

    // إنشاء مؤشر التحديث
    if (!document.querySelector('.pull-refresh-indicator')) {
        const refreshDiv = document.createElement('div');
        refreshDiv.className = 'pull-refresh-indicator';
        refreshDiv.innerHTML = '<i class="fas fa-sync-alt"></i>';
        document.body.appendChild(refreshDiv);
    }

    // تمكين فقط في مناطق المحتوى الرئيسية
    if (document.querySelector('.mobile-content')) {
        document.addEventListener('touchstart', function(e) {
            touchStartY = e.touches[0].clientY;
        }, { passive: true });

        document.addEventListener('touchmove', function(e) {
            if (document.scrollingElement.scrollTop === 0) {
                touchEndY = e.touches[0].clientY;
                const distance = touchEndY - touchStartY;

                if (distance > 50 && distance < minPullDistance) {
                    const refreshDiv = document.querySelector('.pull-refresh-indicator');
                    refreshDiv.style.top = (distance / 3) + 'px';
                }
            }
        }, { passive: true });

        document.addEventListener('touchend', function() {
            const distance = touchEndY - touchStartY;
            const refreshDiv = document.querySelector('.pull-refresh-indicator');

            if (distance >= minPullDistance && document.scrollingElement.scrollTop === 0) {
                // إظهار تأثير التحديث
                refreshDiv.classList.add('visible', 'refreshing');

                // إعادة تحميل الصفحة بعد انتهاء التأثير
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                // إعادة تعيين الموضع
                refreshDiv.style.top = '-60px';
            }

            // إعادة تعيين القيم
            touchStartY = 0;
            touchEndY = 0;
        }, { passive: true });
    }
}

// تحديث مؤشر اتصال الإنترنت
function updateOnlineStatus() {
    const isOnline = navigator.onlineStatus !== undefined ? navigator.onlineStatus : navigator.onLine;

    // إنشاء مؤشر عدم الاتصال إذا لم يكن موجودًا
    if (!document.querySelector('.mobile-offline-indicator')) {
        const offlineDiv = document.createElement('div');
        offlineDiv.className = 'mobile-offline-indicator';
        offlineDiv.innerHTML = '<i class="fas fa-wifi-slash"></i> أنت غير متصل بالإنترنت';
        document.body.appendChild(offlineDiv);
    }

    const offlineIndicator = document.querySelector('.mobile-offline-indicator');

    if (!isOnline) {
        offlineIndicator.classList.add('show');
        showMobileToast('<i class="fas fa-exclamation-triangle"></i> أنت غير متصل بالإنترنت حاليًا', 'error');
    } else {
        offlineIndicator.classList.remove('show');
    }
}

// إظهار رسائل التوست المتحركة
window.showMobileToast = function(message, type = 'info') {
    // إنشاء حاوية التوست إذا لم تكن موجودة
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '1100';
        document.body.appendChild(toastContainer);
    }

    // إنشاء عنصر التوست
    const toast = document.createElement('div');
    toast.className = `toast align-items-center border-0 ${type === 'error' ? 'bg-danger' : type === 'success' ? 'bg-success' : type === 'warning' ? 'bg-warning' : 'bg-dark'}`;
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

// التحقق من نوع الجهاز
window.isMobileDevice = function() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) || window.innerWidth < 768;
};

// التوجيه إلى نسخة الموبايل إذا لزم الأمر
window.checkAndRedirectToMobile = function() {
    if (window.isMobileDevice()) {
        // التحقق مما إذا كنا بالفعل على نسخة الموبايل
        if (!window.location.pathname.includes('/mobile/')) {
            const path = window.location.pathname;
            // تحويل المسارات العادية إلى مسارات للموبايل
            let mobilePath = path;

            // ربط المسارات العادية بمسارات الموبايل
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

            // التعليق لمنع إعادة التوجيه التلقائي لأغراض التطوير
            // window.location.href = mobilePath + window.location.search;
        }
    } else {
        // التحقق مما إذا كنا على نسخة الموبايل ولكن باستخدام جهاز كمبيوتر
        if (window.location.pathname.includes('/mobile/')) {
            // تحويل مسارات الموبايل إلى مسارات عادية
            const path = window.location.pathname;
            let desktopPath = path.replace('/mobile', '');

            if (desktopPath === '') {
                desktopPath = '/';
            }

            // التعليق لمنع إعادة التوجيه التلقائي لأغراض التطوير
            // window.location.href = desktopPath + window.location.search;
        }
    }
};

// تفعيل التمرير السلس
function initSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]:not([data-toggle]):not([data-bs-toggle])').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();

            const targetId = this.getAttribute('href');
            if (targetId === '#') return;

            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// تفعيل تحميل الصور بشكل تدريجي
function initLazyLoading() {
    // إضافة مراقب تقاطع للصور
    if ('IntersectionObserver' in window) {
        const lazyImages = document.querySelectorAll('img[data-src]');

        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.add('fade-in');
                    observer.unobserve(img);
                }
            });
        });

        lazyImages.forEach(img => {
            imageObserver.observe(img);
        });
    } else {
        // البديل لمتصفحات لا تدعم IntersectionObserver
        const lazyImages = document.querySelectorAll('img[data-src]');

        lazyImages.forEach(img => {
            img.src = img.dataset.src;
        });
    }
}

// تفعيل مبدّل الوضع المظلم
function initThemeToggle() {
    const themeToggle = document.getElementById('themeToggle');

    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const icon = this.querySelector('i');

            if (document.documentElement.classList.contains('dark-mode')) {
                document.documentElement.classList.remove('dark-mode');
                icon.classList.remove('fa-sun');
                icon.classList.add('fa-moon');
                localStorage.setItem('theme', 'light');
                showMobileToast('<i class="fas fa-sun"></i> تم تفعيل الوضع النهاري', 'info');
            } else {
                document.documentElement.classList.add('dark-mode');
                icon.classList.remove('fa-moon');
                icon.classList.add('fa-sun');
                localStorage.setItem('theme', 'dark');
                showMobileToast('<i class="fas fa-moon"></i> تم تفعيل الوضع الليلي', 'info');
            }
        });

        // تطبيق السمة المحفوظة عند التحميل
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'dark') {
            document.documentElement.classList.add('dark-mode');
            const icon = themeToggle.querySelector('i');
            if (icon) {
                icon.classList.remove('fa-moon');
                icon.classList.add('fa-sun');
            }
        }
    }
}

// تفعيل تأثيرات الرسوم المتحركة
function initAnimations() {
    // إضافة فئات التأخير للعناصر المتتالية
    const contentElements = document.querySelectorAll('.mobile-card, .service-card, .booking-card, .notification-item');

    contentElements.forEach((element, index) => {
        const delay = index % 5;
        element.classList.add('fade-in', `animate-delay-${delay}`);

        // إزالة فئات الرسوم المتحركة بعد الانتهاء
        setTimeout(() => {
            element.classList.remove('fade-in', `animate-delay-${delay}`);
        }, 1000);
    });
}

// تحديث عداد الإشعارات
function updateNotificationCount() {
    const unreadItems = document.querySelectorAll('.notification-item.unread').length;
    const badges = document.querySelectorAll('.notification-badge');

    badges.forEach(badge => {
        if (unreadItems > 0) {
            badge.textContent = unreadItems;
            badge.style.display = 'flex';
        } else {
            badge.style.display = 'none';
        }
    });
}

// تهيئة البنرات المتحركة
function initBannerSlider() {
    const bannerSliders = document.querySelectorAll('.banner-slider');
    if (bannerSliders.length === 0) return;

    bannerSliders.forEach(slider => {
        const slides = slider.querySelectorAll('.banner-slide');
        if (slides.length <= 1) return; // لا داعي للتمرير إذا كان هناك شريحة واحدة أو أقل

        const slidesContainer = slider.querySelector('.banner-slides');
        const indicators = slider.querySelectorAll('.banner-indicator');
        const prevButton = slider.querySelector('.banner-prev');
        const nextButton = slider.querySelector('.banner-next');

        let currentSlide = 0;
        const slideCount = slides.length;
        let autoSlideInterval;

        // تحديث مؤشرات الشرائح
        function updateIndicators() {
            if (!indicators.length) return;

            indicators.forEach((indicator, index) => {
                if (index === currentSlide) {
                    indicator.classList.add('active');
                } else {
                    indicator.classList.remove('active');
                }
            });
        }

        // الانتقال إلى الشريحة
        function goToSlide(slideIndex) {
            currentSlide = slideIndex;
            if (slidesContainer) {
                slidesContainer.style.transform = `translateX(-${currentSlide * 100}%)`;
                updateIndicators();
            }
        }

        // الانتقال للشريحة التالية
        function nextSlide() {
            currentSlide = (currentSlide + 1) % slideCount;
            goToSlide(currentSlide);
        }

        // الانتقال للشريحة السابقة
        function prevSlide() {
            currentSlide = (currentSlide - 1 + slideCount) % slideCount;
            goToSlide(currentSlide);
        }

        // إضافة أحداث النقر للمؤشرات
        if (indicators.length) {
            indicators.forEach((indicator, index) => {
                indicator.addEventListener('click', () => {
                    goToSlide(index);
                    resetAutoSlide();
                });
            });
        }

        // إضافة أحداث للأزرار
        if (nextButton) {
            nextButton.addEventListener('click', () => {
                nextSlide();
                resetAutoSlide();
            });
        }

        if (prevButton) {
            prevButton.addEventListener('click', () => {
                prevSlide();
                resetAutoSlide();
            });
        }

        // التمرير التلقائي - تغيير كل 5 ثواني
        function startAutoSlide() {
            autoSlideInterval = setInterval(nextSlide, 5000); // 5000 مللي ثانية = 5 ثواني
        }

        // إعادة ضبط المؤقت
        function resetAutoSlide() {
            clearInterval(autoSlideInterval);
            startAutoSlide();
        }

        // بدء التمرير التلقائي
        startAutoSlide();

        // إيقاف التمرير التلقائي عند التفاعل
        slider.addEventListener('mouseenter', () => {
            clearInterval(autoSlideInterval);
        });

        // استئناف التمرير التلقائي بعد انتهاء التفاعل
        slider.addEventListener('mouseleave', () => {
            startAutoSlide();
        });

        // دعم السحب للأجهزة اللمسية
        let touchStartX = 0;
        let touchEndX = 0;

        if (slidesContainer) {
            slidesContainer.addEventListener('touchstart', (e) => {
                touchStartX = e.changedTouches[0].screenX;
                clearInterval(autoSlideInterval);
            }, { passive: true });

            slidesContainer.addEventListener('touchend', (e) => {
                touchEndX = e.changedTouches[0].screenX;
                handleSwipe();
                startAutoSlide();
            }, { passive: true });
        }

        function handleSwipe() {
            // حساب الفرق بين نقطة البداية ونقطة النهاية
            const difference = touchStartX - touchEndX;
            const threshold = 50; // الحد الأدنى للمسافة للاعتراف بالسحب

            if (Math.abs(difference) < threshold) return;

            if (difference > 0) {
                nextSlide(); // سحب لليسار
            } else {
                prevSlide(); // سحب لليمين
            }
        }
    });
}

// إضافة بعض التفاعلات الإضافية للعناصر عند تحميل الصفحة
document.addEventListener('DOMContentLoaded', function() {
    // إضافة تأثير انتقالي عند تحميل الصفحة
    document.body.classList.add('page-transition-in');
    setTimeout(() => {
        document.body.classList.remove('page-transition-in');
    }, 300);

    // تشغيل تأثيرات الرسوم المتحركة بعد تحميل الصفحة
    setTimeout(initAnimations, 100);
});