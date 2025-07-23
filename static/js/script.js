// static/js/script.js
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('pdf-form');
    const previewContainer = document.getElementById('preview-container');
    const loadingSpinner = document.getElementById('loading-spinner');
    const themeToggle = document.getElementById('theme-toggle');
    const documentElement = document.documentElement;

    // --- Theme Management ---
    const applyTheme = (theme) => {
        documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        themeToggle.checked = theme === 'dark';
    };

    themeToggle.addEventListener('change', () => {
        const newTheme = themeToggle.checked ? 'dark' : 'light';
        applyTheme(newTheme);
    });

    // Apply saved theme on initial load
    const savedTheme = localStorage.getItem('theme') || 'light';
    applyTheme(savedTheme);
    
    // --- Debounce Function ---
    const debounce = (func, wait) => {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    };

    // --- Preview Update Logic ---
    const updatePreview = () => {
        loadingSpinner.classList.remove('hidden');
        previewContainer.innerHTML = ''; 
        previewContainer.appendChild(loadingSpinner);

        const formData = new FormData(form);

        fetch('/preview', {
            method: 'POST',
            body: formData,
        })
        .then(response => response.ok ? response.json() : response.json().then(err => { throw new Error(err.error) }))
        .then(data => {
            loadingSpinner.classList.add('hidden');
            previewContainer.innerHTML = '';
            
            if (data.pages && data.pages.length > 0) {
                data.pages.forEach((pageDataUrl, index) => {
                    const pageWrapper = document.createElement('div');
                    pageWrapper.className = 'preview-page-wrapper';
                    const pageLabel = document.createElement('p');
                    pageLabel.className = 'preview-page-label';
                    pageLabel.textContent = `Page ${index + 1}`;
                    const img = document.createElement('img');
                    img.src = pageDataUrl;
                    img.alt = `Preview of Page ${index + 1}`;
                    img.className = 'preview-image';
                    
                    pageWrapper.appendChild(pageLabel);
                    pageWrapper.appendChild(img);
                    previewContainer.appendChild(pageWrapper);
                });
            } else {
                previewContainer.textContent = 'No preview available.';
            }
        })
        .catch(error => {
            console.error('Error fetching preview:', error);
            loadingSpinner.classList.add('hidden');
            previewContainer.innerHTML = `<p style="color:red; font-weight:500;">Error: ${error.message}</p>`;
        });
    };

    // --- Attach Event Listeners ---
    const debouncedUpdatePreview = debounce(updatePreview, 500);
    const inputs = form.querySelectorAll('.auto-update');
    inputs.forEach(input => {
        const eventType = (input.type === 'text' || input.type === 'number') ? 'input' : 'change';
        input.addEventListener(eventType, debouncedUpdatePreview);
    });
    
    // Initial preview on page load
    updatePreview();
});