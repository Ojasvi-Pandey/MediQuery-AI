// static/js/main.js - Main JavaScript file

// Auto-dismiss alerts after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });
});

// File input label update
const fileInput = document.getElementById('file');
if (fileInput) {
    fileInput.addEventListener('change', function(e) {
        const fileName = e.target.files[0]?.name;
        if (fileName) {
            const label = document.querySelector('.file-text');
            if (label) {
                label.textContent = fileName;
            }
        }
    });
}

// Confirm before logout
const logoutLinks = document.querySelectorAll('a[href*="logout"]');
logoutLinks.forEach(link => {
    link.addEventListener('click', function(e) {
        if (!confirm('Are you sure you want to logout?')) {
            e.preventDefault();
        }
    });
});

// Form validation
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (form) {
        form.addEventListener('submit', function(e) {
            const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');
            let isValid = true;
            
            inputs.forEach(input => {
                if (!input.value.trim()) {
                    isValid = false;
                    input.style.borderColor = 'red';
                } else {
                    input.style.borderColor = '';
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                alert('Please fill in all required fields');
            }
        });
    }
}

// Password match validation for registration
const registerForm = document.querySelector('form[action*="register"]');
if (registerForm) {
    registerForm.addEventListener('submit', function(e) {
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirm_password').value;
        
        if (password !== confirmPassword) {
            e.preventDefault();
            alert('Passwords do not match!');
            document.getElementById('confirm_password').style.borderColor = 'red';
        }
    });
}

// Loading indicator for file uploads
const uploadForms = document.querySelectorAll('form[enctype="multipart/form-data"]');
uploadForms.forEach(form => {
    form.addEventListener('submit', function() {
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Uploading...';
            submitBtn.style.opacity = '0.6';
        }
    });
});

// Question textarea auto-resize
const questionTextarea = document.getElementById('question');
if (questionTextarea) {
    questionTextarea.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });
}

// Feedback functions
function markCorrect(answerId) {
    if (!confirm('Mark this answer as correct?')) return;
    
    fetch('/feedback', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            answer_id: answerId,
            is_correct: true
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Answer marked as correct!');
            location.reload();
        } else {
            alert('Error: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred. Please try again.');
    });
}

function editAnswer(answerId) {
    const answerElement = document.getElementById('answer-content-' + answerId);
    if (!answerElement) return;
    
    const currentAnswer = answerElement.textContent.trim();
    const newAnswer = prompt('Edit the answer:', currentAnswer);
    
    if (newAnswer && newAnswer !== currentAnswer) {
        fetch('/feedback', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                answer_id: answerId,
                is_correct: false,
                edited_answer: newAnswer
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                answerElement.textContent = newAnswer;
                alert('Answer updated successfully!');
                location.reload();
            } else {
                alert('Error: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred. Please try again.');
        });
    }
}

// Tab functionality for history page
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    const selectedTab = document.getElementById(tabName + '-tab');
    const clickedButton = event.target;
    
    if (selectedTab) selectedTab.classList.add('active');
    if (clickedButton) clickedButton.classList.add('active');
}

// Export functions to global scope for inline handlers
window.markCorrect = markCorrect;
window.editAnswer = editAnswer;
window.showTab = showTab;