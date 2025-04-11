// Main JavaScript file for the Local Services Platform

document.addEventListener('DOMContentLoaded', function() {
    // Mobile menu toggle
    const navbarToggle = document.querySelector('.navbar-toggle');
    const navbarMenu = document.querySelector('.navbar-menu');

    if (navbarToggle && navbarMenu) {
        navbarToggle.addEventListener('click', function() {
            navbarMenu.classList.toggle('active');
        });
    }

    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    if (forms.length > 0) {
        Array.from(forms).forEach(form => {
            form.addEventListener('submit', event => {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                form.classList.add('was-validated');
            }, false);
        });
    }

    // تهيئة عناصر التقييم في الصفحة
    initRatingSystem();

    // تهيئة نوافذ التقييم المنبثقة
    initReviewModals();
});

// دالة لعرض تقييمات النجوم في الصفحة
function initRatingSystem() {
    const ratingElements = document.querySelectorAll('.rating-display');
    if (ratingElements.length > 0) {
        ratingElements.forEach(element => {
            const rating = parseFloat(element.getAttribute('data-rating') || 0);
            const maxRating = 5;
            let starsHtml = '';

            for (let i = 1; i <= maxRating; i++) {
                if (i <= rating) {
                    starsHtml += '<i class="fas fa-star rating-star"></i>';
                } else if (i - 0.5 <= rating) {
                    starsHtml += '<i class="fas fa-star-half-alt rating-star"></i>';
                } else {
                    starsHtml += '<i class="far fa-star rating-star"></i>';
                }
            }
            element.innerHTML = starsHtml;
        });
    }
}

// دالة لتهيئة نوافذ التقييم المنبثقة
function initReviewModals() {
    // البحث عن زر إضافة تقييم
    const reviewButtons = document.querySelectorAll('.add-review');
    if (!reviewButtons.length) return;

    // البحث عن نافذة التقييم
    const reviewModalElement = document.getElementById('reviewModal');
    if (!reviewModalElement) {
        console.log("لم يتم العثور على نافذة التقييم في الصفحة الحالية");
        return;
    }

    // تهيئة نافذة التقييم
    let reviewModal;
    try {
        reviewModal = new bootstrap.Modal(reviewModalElement);
    } catch (e) {
        console.error('خطأ في تهيئة نافذة التقييم:', e);
        return;
    }

    // إضافة حدث النقر على زر إضافة تقييم
    reviewButtons.forEach(btn => {
        btn.addEventListener('click', async function() {
            const serviceId = this.getAttribute('data-service-id');

            // التحقق من إمكانية التقييم عبر API
            try {
                const response = await fetch(`/api/check_completed_booking/${serviceId}`);
                const data = await response.json();

                if (!data.has_completed) {
                    alert('لا يمكنك تقييم هذه الخدمة حتى تكتمل عملية الحجز.');
                    return;
                }

                if (data.has_review) {
                    alert('لقد قمت بتقييم هذه الخدمة بالفعل.');
                    return;
                }

                // تعيين معرف الخدمة في النموذج
                document.getElementById('modal_service_id').value = serviceId;

                // إعادة تعيين التقييم
                const ratingInput = document.getElementById('rating_input');
                if (ratingInput) ratingInput.value = 0;

                // إعادة تعيين النجوم
                const stars = document.querySelectorAll('.star-rating');
                if (stars.length) {
                    stars.forEach(s => {
                        s.className = 'far fa-star star-rating';
                    });
                }

                // عرض النافذة
                reviewModal.show();

            } catch (error) {
                console.error('خطأ في التحقق من إمكانية التقييم:', error);
                alert('حدث خطأ أثناء التحقق من إمكانية التقييم. الرجاء المحاولة مرة أخرى.');
            }
        });
    });

    // معالجة تقييم النجوم
    const stars = document.querySelectorAll('.star-rating');
    const ratingInput = document.getElementById('rating_input');

    if (stars.length && ratingInput) {
        // إضافة الاستماع إلى حدث النقر لكل نجمة
        stars.forEach(star => {
            star.addEventListener('click', function() {
                const value = parseInt(this.getAttribute('data-value'));
                ratingInput.value = value;

                // تحديث شكل النجوم
                stars.forEach(s => {
                    const starValue = parseInt(s.getAttribute('data-value'));
                    if (starValue <= value) {
                        s.className = 'fas fa-star star-rating text-warning';
                    } else {
                        s.className = 'far fa-star star-rating';
                    }
                });
            });

            // إضافة تأثير التحويم
            star.addEventListener('mouseover', function() {
                const value = parseInt(this.getAttribute('data-value'));

                stars.forEach(s => {
                    const starValue = parseInt(s.getAttribute('data-value'));
                    if (starValue <= value) {
                        s.className = 'fas fa-star star-rating text-warning';
                    } else {
                        s.className = 'far fa-star star-rating';
                    }
                });
            });
        });

        // استعادة حالة النجوم عند الخروج من منطقة التقييم
        const ratingContainer = document.querySelector('.rating-input-container');
        if (ratingContainer) {
            ratingContainer.addEventListener('mouseleave', function() {
                const value = parseInt(ratingInput.value) || 0;

                stars.forEach(s => {
                    const starValue = parseInt(s.getAttribute('data-value'));
                    if (starValue <= value) {
                        s.className = 'fas fa-star star-rating text-warning';
                    } else {
                        s.className = 'far fa-star star-rating';
                    }
                });
            });
        }
    }

    // التحقق من صحة نموذج التقييم عند الإرسال
    const reviewForm = document.getElementById('reviewForm');
    if (reviewForm) {
        reviewForm.addEventListener('submit', function(e) {
            const rating = parseInt(ratingInput.value) || 0;
            const comment = document.querySelector('#reviewForm textarea[name="comment"]').value.trim();

            if (rating === 0 || rating > 5) {
                e.preventDefault();
                alert('يرجى تحديد تقييم بين 1 و 5 نجوم');
                return false;
            }

            if (comment.length < 10) {
                e.preventDefault();
                alert('يرجى كتابة تعليق مناسب (10 أحرف على الأقل)');
                return false;
            }

            return true;
        });
    }
}
    // Datetime picker initialization for booking forms
    const datetimeFields = document.querySelectorAll('input[type="datetime-local"]');
    if (datetimeFields.length > 0) {
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');

        const minDateTime = `${year}-${month}-${day}T${hours}:${minutes}`;

        datetimeFields.forEach(field => {
            field.setAttribute('min', minDateTime);
        });
    }

    // Toggle admin controls (active/inactive status)
    const toggleButtons = document.querySelectorAll('.toggle-status');
    if (toggleButtons.length > 0) {
        toggleButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();

                const url = this.getAttribute('data-url');
                const statusElement = this.querySelector('.status-text');
                const icon = this.querySelector('i');

                fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Update the button text and icon
                        if (data.active) {
                            statusElement.textContent = 'مفعل';
                            icon.className = 'fas fa-toggle-on text-success';
                        } else {
                            statusElement.textContent = 'معطل';
                            icon.className = 'fas fa-toggle-off text-danger';
                        }

                        // Show success message
                        showAlert('success', data.message);
                    } else {
                        showAlert('danger', data.message);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showAlert('danger', 'حدث خطأ أثناء تحديث الحالة');
                });
            });
        });
    }

    // Function to show alerts
    function showAlert(type, message) {
        const alertContainer = document.querySelector('.alert-container');
        if (alertContainer) {
            const alert = document.createElement('div');
            alert.className = `alert alert-${type} alert-dismissible fade show`;
            alert.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            `;

            alertContainer.appendChild(alert);

            // Auto-dismiss after 5 seconds
            setTimeout(() => {
                alert.classList.remove('show');
                setTimeout(() => {
                    alertContainer.removeChild(alert);
                }, 150);
            }, 5000);
        }
    }

    // Search form functionality
    const searchForm = document.querySelector('#search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            // Prevent empty searches
            const searchInput = this.querySelector('input[name="query"]');
            if (searchInput && !searchInput.value.trim()) {
                e.preventDefault();
                showAlert('warning', 'الرجاء إدخال كلمة للبحث');
            }
        });
    }

    // دالة لتهيئة نظام التقييم في النوافذ المنبثقة
    function initReviewModals() {
        const reviewModalElement = document.getElementById('reviewModal');
        if (!reviewModalElement) {
            console.log('لم يتم العثور على نافذة التقييم في الصفحة الحالية');
            return;
        }

        let reviewModal;
        try {
            reviewModal = new bootstrap.Modal(reviewModalElement);
            console.log('تم تهيئة نافذة التقييم بنجاح');
        } catch (e) {
            console.error('خطأ في تهيئة نافذة التقييم:', e);
            return;
        }

        // تحديد زر التقييم وإضافة حدث النقر عليه
        document.querySelectorAll('.review-button, .add-review').forEach(btn => {
            btn.addEventListener('click', async function(e) {
                e.preventDefault();
                const serviceId = this.getAttribute('data-service-id');
                console.log('تم النقر على زر التقييم للخدمة: ' + serviceId);

                // التحقق من إمكانية التقييم عبر API
                try {
                    const response = await fetch(`/api/check_completed_booking/${serviceId}`);
                    const data = await response.json();

                    if (!data.has_completed) {
                        showModalOrAlert('warning', 'لا يمكنك تقييم هذه الخدمة حتى تكتمل عملية الحجز.');
                        return;
                    }

                    if (data.has_review) {
                        showModalOrAlert('info', 'لقد قمت بتقييم هذه الخدمة بالفعل.');
                        return;
                    }

                    // تعيين معرف الخدمة في النموذج
                    const serviceIdInput = document.getElementById('modal_service_id');
                    if (serviceIdInput) {
                        serviceIdInput.value = serviceId;
                    }

                    // عرض النافذة
                    reviewModal.show();

                    // ضمان ظهور النافذة على الشاشة
                    setTimeout(() => {
                        reviewModalElement.style.display = 'block';
                        document.body.classList.add('modal-open');

                        // إضافة backdrop إذا لم يكن موجوداً
                        if (!document.querySelector('.modal-backdrop')) {
                            const backdrop = document.createElement('div');
                            backdrop.className = 'modal-backdrop fade show';
                            document.body.appendChild(backdrop);
                        }
                    }, 100);
                } catch (error) {
                    console.error('خطأ في التحقق من إمكانية التقييم:', error);
                    showModalOrAlert('danger', 'حدث خطأ أثناء التحقق من إمكانية التقييم. الرجاء المحاولة مرة أخرى.');
                }
            });
        });

        // معالجة تقييم النجوم
        const stars = document.querySelectorAll('.star-rating');
        const ratingInput = document.getElementById('rating_input');

        if (stars.length && ratingInput) {
            console.log('تم تهيئة نظام تقييم النجوم');

            // ضمان أن كل النجوم فارغة في البداية
            stars.forEach(s => {
                s.className = 'far fa-star star-rating';
            });

            // إضافة الاستماع إلى حدث النقر لكل نجمة
            stars.forEach(star => {
                star.addEventListener('click', function() {
                    const value = parseInt(this.getAttribute('data-value'));
                    ratingInput.value = value;
                    console.log('تم اختيار تقييم: ' + value);

                    // تحديث شكل النجوم
                    stars.forEach(s => {
                        const starValue = parseInt(s.getAttribute('data-value'));
                        if (starValue <= value) {
                            s.className = 'fas fa-star star-rating text-warning';
                        } else {
                            s.className = 'far fa-star star-rating';
                        }
                    });
                });

                // إضافة تأثير التحويم
                star.addEventListener('mouseover', function() {
                    const value = parseInt(this.getAttribute('data-value'));

                    stars.forEach(s => {
                        const starValue = parseInt(s.getAttribute('data-value'));
                        if (starValue <= value) {
                            s.className = 'fas fa-star star-rating text-warning';
                        } else {
                            s.className = 'far fa-star star-rating';
                        }
                    });
                });
            });

            // استعادة حالة النجوم عند الخروج من منطقة التقييم
            const ratingContainer = document.querySelector('.rating-input-container');
            if (ratingContainer) {
                ratingContainer.addEventListener('mouseleave', function() {
                    const value = parseInt(ratingInput.value) || 0;

                    stars.forEach(s => {
                        const starValue = parseInt(s.getAttribute('data-value'));
                        if (starValue <= value) {
                            s.className = 'fas fa-star star-rating text-warning';
                        } else {
                            s.className = 'far fa-star star-rating';
                        }
                    });
                });
            }
        }

        // التحقق من صحة النموذج عند الإرسال
        const reviewForm = document.getElementById('reviewForm');
        if (reviewForm) {
            reviewForm.addEventListener('submit', function(e) {
                const rating = parseInt(ratingInput.value) || 0;
                const comment = document.getElementById('comment').value.trim();

                if (rating === 0 || rating > 5) {
                    e.preventDefault();
                    showModalOrAlert('warning', 'يرجى تحديد تقييم بين 1 و 5 نجوم');
                    return false;
                }

                if (comment.length < 10) {
                    e.preventDefault();
                    showModalOrAlert('warning', 'يرجى كتابة تعليق مناسب (10 أحرف على الأقل)');
                    return false;
                }

                console.log('تم إرسال نموذج التقييم بنجاح');
                return true;
            });
        }
    }

    // دالة لعرض تنبيه أو نافذة منبثقة
    function showModalOrAlert(type, message) {
        // عرض تنبيه عادي إذا كنا على الكمبيوتر
        if (window.innerWidth >= 768) {
            alert(message);
            return;
        }

        // عرض تنبيه جميل إذا كنا على الموبايل
        const alertBox = document.createElement('div');
        alertBox.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
        alertBox.style.zIndex = '9999';
        alertBox.style.maxWidth = '90%';
        alertBox.style.boxShadow = '0 4px 15px rgba(0,0,0,0.1)';
        alertBox.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        document.body.appendChild(alertBox);

        setTimeout(() => {
            alertBox.classList.remove('show');
            setTimeout(() => alertBox.remove(), 300);
        }, 3000);
    }

    // تهيئة عرض التقييمات
    function initRatingDisplays() {
        const ratingElements = document.querySelectorAll('.rating-display');
        if (ratingElements.length > 0) {
            ratingElements.forEach(element => {
                const rating = parseFloat(element.getAttribute('data-rating') || 0);
                const maxRating = 5;
                let starsHtml = '';

                for (let i = 1; i <= maxRating; i++) {
                    if (i <= rating) {
                        starsHtml += '<i class="fas fa-star rating-star text-warning"></i>';
                    } else if (i - 0.5 <= rating) {
                        starsHtml += '<i class="fas fa-star-half-alt rating-star text-warning"></i>';
                    } else {
                        starsHtml += '<i class="far fa-star rating-star text-warning"></i>';
                    }
                }

                element.innerHTML = starsHtml;
            });
        }
    }

    // تنفيذ تهيئة التقييمات
    initRatingDisplays();
    initReviewModals();

    // تهيئة نجوم التقييم
    function initRatingStars() {
        const ratingContainers = document.querySelectorAll('.rating-input-container');

        ratingContainers.forEach(container => {
            const stars = container.querySelectorAll('.star-rating');
            const ratingInput = container.querySelector('input[type="hidden"]');

            if (stars.length > 0 && ratingInput) {
                stars.forEach(star => {
                    star.addEventListener('click', function() {
                        const value = parseInt(this.getAttribute('data-value'));
                        ratingInput.value = value;

                        // تحديث مظهر النجوم
                        stars.forEach(s => {
                            const starValue = parseInt(s.getAttribute('data-value'));
                            if (starValue <= value) {
                                s.classList.remove('far');
                                s.classList.add('fas');
                            } else {
                                s.classList.remove('fas');
                                s.classList.add('far');
                            }
                        });
                    });

                    // إضافة تأثير عند المرور على النجوم
                    star.addEventListener('mouseover', function() {
                        const value = parseInt(this.getAttribute('data-value'));

                        stars.forEach(s => {
                            const starValue = parseInt(s.getAttribute('data-value'));
                            if (starValue <= value) {
                                s.classList.remove('far');
                                s.classList.add('fas');
                            }
                        });
                    });

                    // استعادة الحالة الأصلية عند إبعاد المؤشر
                    star.addEventListener('mouseout', function() {
                        const currentRating = parseInt(ratingInput.value) || 0;

                        stars.forEach(s => {
                            const starValue = parseInt(s.getAttribute('data-value'));
                            if (starValue <= currentRating) {
                                s.classList.remove('far');
                                s.classList.add('fas');
                            } else {
                                s.classList.remove('fas');
                                s.classList.add('far');
                            }
                        });
                    });
                });
            }
        });
    }

    // فتح نافذة التقييم عند الضغط على زر التقييم
    function setupReviewModal() {
        const reviewButtons = document.querySelectorAll('.open-review-modal');

        reviewButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const serviceId = this.getAttribute('data-service-id');
                const reviewModal = document.getElementById('reviewModal');

                if (serviceId && reviewModal) {
                    const modalServiceIdInput = document.getElementById('modal_service_id');
                    if (modalServiceIdInput) {
                        modalServiceIdInput.value = serviceId;
                    }

                    // استخدام الطريقة الحديثة لإظهار النوافذ المنبثقة
                    const bsModal = new bootstrap.Modal(reviewModal);
                    bsModal.show();
                } else {
                    console.log("لم يتم العثور على نافذة التقييم في الصفحة الحالية");
                }
            });
        });
    }

    // استدعاء الدوال عند تحميل الصفحة
    try {
        initRatingStars();
    } catch(e) {
        console.error("خطأ في تهيئة نجوم التقييم:", e);
    }

    try {
        setupReviewModal();
    } catch(e) {
        console.error("خطأ في تهيئة نافذة التقييم:", e);
    }

    try {
        setupBookingStatus();
    } catch(e) {
        console.error("خطأ في تهيئة حالة الحجز:", e);
    }

    try {
        setupServiceStatus();
    } catch(e) {
        console.error("خطأ في تهيئة حالة الخدمة:", e);
    }

    try {
        setupPaymentForms();
    } catch(e) {
        console.error("خطأ في تهيئة نماذج الدفع:", e);
    }

    try {
        setupProviderControls();
    } catch(e) {
        console.error("خطأ في تهيئة أدوات مزود الخدمة:", e);
    }

    try {
        setupNotifications();
    } catch(e) {
        console.error("خطأ في تهيئة الإشعارات:", e);
    }

    try {
        setupFilePreview();
    } catch(e) {
        console.error("خطأ في تهيئة معاينة الملفات:", e);
    }

    try {
        setupForms();
    } catch(e) {
        console.error("خطأ في تهيئة النماذج:", e);
    }

    // التحقق من إمكانية التقييم وإظهار النافذة
    function checkAndShowReviewModal(serviceId) {
        console.log('التحقق من إمكانية التقييم للخدمة:', serviceId);

        // تحقق من وجود نافذة التقييم في الصفحة الحالية
        const modalElement = document.getElementById('reviewModal');
        if (!modalElement) {
            console.error('لم يتم العثور على نافذة التقييم في الصفحة الحالية');
            showAlert('danger', 'لا يمكن فتح نافذة التقييم، يرجى تحديث الصفحة');
            return;
        }

        fetch('/api/check_completed_booking/' + serviceId)
            .then(response => response.json())
            .then(data => {
                if (!data.has_completed) {
                    showAlert('warning', 'لا يمكنك تقييم هذه الخدمة حتى تكتمل عملية الحجز.');
                    return;
                }

                if (data.has_review) {
                    showAlert('info', 'لقد قمت بتقييم هذه الخدمة بالفعل.');
                    return;
                }

                // تعيين معرف الخدمة في النموذج
                document.getElementById('modal_service_id').value = serviceId;

                // إنشاء وإظهار نافذة التقييم
                try {
                    const reviewModal = new bootstrap.Modal(modalElement);
                    reviewModal.show();

                    // تأكيد من أن النافذة المنبثقة تظهر بشكل صحيح
                    modalElement.classList.add('show');
                    document.body.classList.add('modal-open');

                    // إضافة backdrop إذا لم يكن موجودًا
                    if (!document.querySelector('.modal-backdrop')) {
                        const backdrop = document.createElement('div');
                        backdrop.className = 'modal-backdrop fade show';
                        document.body.appendChild(backdrop);
                    }
                } catch (e) {
                    console.error('خطأ في فتح نافذة التقييم:', e);
                    showAlert('danger', 'حدث خطأ أثناء فتح نافذة التقييم');
                }
            })
            .catch(error => {
                console.error('خطأ في التحقق من حالة الحجز:', error);
                showAlert('danger', 'حدث خطأ أثناء التحقق من إمكانية التقييم');
            });
    }
});