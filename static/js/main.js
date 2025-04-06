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
    
    // Service rating display
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
});
