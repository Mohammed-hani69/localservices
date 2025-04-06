// Payment processing JavaScript file

document.addEventListener('DOMContentLoaded', function() {
    const paymentForm = document.getElementById('payment-form');
    const paymentMethodSelect = document.getElementById('payment_method');
    const cardDetailsSection = document.getElementById('card-details');
    
    if (paymentForm && paymentMethodSelect && cardDetailsSection) {
        // Function to toggle card details visibility based on payment method
        function toggleCardDetails() {
            const selectedMethod = paymentMethodSelect.value;
            if (selectedMethod === 'credit_card' || selectedMethod === 'debit_card') {
                cardDetailsSection.style.display = 'block';
                // Make card fields required
                document.querySelectorAll('#card-details input').forEach(input => {
                    input.setAttribute('required', '');
                });
            } else {
                cardDetailsSection.style.display = 'none';
                // Remove required attribute from card fields
                document.querySelectorAll('#card-details input').forEach(input => {
                    input.removeAttribute('required');
                });
            }
        }
        
        // Initial call to set the correct state
        toggleCardDetails();
        
        // Add event listener for change
        paymentMethodSelect.addEventListener('change', toggleCardDetails);
        
        // Handle form submission (mock payment processing)
        paymentForm.addEventListener('submit', function(e) {
            const selectedMethod = paymentMethodSelect.value;
            
            // Validate card details if credit/debit card is selected
            if ((selectedMethod === 'credit_card' || selectedMethod === 'debit_card')) {
                const cardNumber = document.getElementById('card_number').value;
                const cardExpiry = document.getElementById('card_expiry').value;
                const cardCvv = document.getElementById('card_cvv').value;
                
                // Validate card number (simple check: 16 digits)
                if (!/^\d{16}$/.test(cardNumber)) {
                    e.preventDefault();
                    showPaymentError('رقم البطاقة غير صحيح. يجب أن يكون 16 رقمًا.');
                    return;
                }
                
                // Validate expiry date (MM/YY format)
                if (!/^(0[1-9]|1[0-2])\/\d{2}$/.test(cardExpiry)) {
                    e.preventDefault();
                    showPaymentError('تاريخ انتهاء البطاقة غير صحيح. استخدم الصيغة MM/YY.');
                    return;
                }
                
                // Validate CVV (3-4 digits)
                if (!/^\d{3,4}$/.test(cardCvv)) {
                    e.preventDefault();
                    showPaymentError('رمز CVV غير صحيح. يجب أن يكون 3 أو 4 أرقام.');
                    return;
                }
            }
            
            // If everything is valid, show processing animation
            showProcessingAnimation();
        });
    }
    
    // Function to show payment error messages
    function showPaymentError(message) {
        const errorContainer = document.getElementById('payment-errors');
        if (errorContainer) {
            errorContainer.textContent = message;
            errorContainer.style.display = 'block';
            
            // Scroll to error message
            errorContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }
    
    // Function to show processing animation
    function showProcessingAnimation() {
        const submitBtn = document.querySelector('#payment-form button[type="submit"]');
        if (submitBtn) {
            // Disable button and change text
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> جاري معالجة الدفع...';
        }
    }
    
    // Card number formatting (add spaces every 4 digits)
    const cardNumberInput = document.getElementById('card_number');
    if (cardNumberInput) {
        cardNumberInput.addEventListener('input', function(e) {
            // Remove non-digits
            let value = this.value.replace(/\D/g, '');
            
            // Limit to 16 digits
            value = value.substring(0, 16);
            
            // Update the input value
            this.value = value;
        });
    }
    
    // Expiry date formatting (MM/YY)
    const expiryInput = document.getElementById('card_expiry');
    if (expiryInput) {
        expiryInput.addEventListener('input', function(e) {
            // Remove non-digits and slashes
            let value = this.value.replace(/[^\d\/]/g, '');
            
            // Add slash after 2 digits if not already there
            if (value.length === 2 && !value.includes('/')) {
                value += '/';
            }
            
            // Limit to MM/YY format (5 chars total)
            value = value.substring(0, 5);
            
            // Update the input value
            this.value = value;
        });
    }
    
    // CVV formatting (3-4 digits only)
    const cvvInput = document.getElementById('card_cvv');
    if (cvvInput) {
        cvvInput.addEventListener('input', function(e) {
            // Remove non-digits
            let value = this.value.replace(/\D/g, '');
            
            // Limit to 4 digits
            value = value.substring(0, 4);
            
            // Update the input value
            this.value = value;
        });
    }
});
