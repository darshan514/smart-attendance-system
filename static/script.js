// Smart Attendance System - JavaScript

document.addEventListener('DOMContentLoaded', function() {
  // Auto-hide alerts
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(alert => {
    setTimeout(() => {
      const bsAlert = new bootstrap.Alert(alert);
      bsAlert.close();
    }, 5000);
  });

  // Delete confirmation
  const deleteForms = document.querySelectorAll('form[action*="/delete_"]');
  deleteForms.forEach(form => {
    form.addEventListener('submit', function(e) {
      if (!confirm('Are you sure you want to delete this? This action cannot be undone.')) {
        e.preventDefault();
      }
    });
  });

  // Image preview on file input
  const fileInput = document.getElementById('fileInput');
  if (fileInput) {
    fileInput.addEventListener('change', function(e) {
      const preview = document.getElementById('preview');
      const file = e.target.files[0];
      
      if (file) {
        const reader = new FileReader();
        reader.onload = function(event) {
          preview.innerHTML = `
            <div class="text-center">
              <img src="${event.target.result}" alt="Preview" style="max-width: 100%; max-height: 300px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
              <p class="text-muted mt-2"><small>${file.name}</small></p>
            </div>
          `;
        };
        reader.readAsDataURL(file);
      }
    });
  }

  // Form validation
  const forms = document.querySelectorAll('form');
  forms.forEach(form => {
    form.addEventListener('submit', function(e) {
      if (!this.checkValidity()) {
        e.preventDefault();
        e.stopPropagation();
      }
      this.classList.add('was-validated');
    });
  });

  // Search input focus (Ctrl+K)
  document.addEventListener('keydown', function(event) {
    if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
      event.preventDefault();
      const searchInput = document.querySelector('input[name="search"]');
      if (searchInput) {
        searchInput.focus();
        searchInput.select();
      }
    }
  });
});
