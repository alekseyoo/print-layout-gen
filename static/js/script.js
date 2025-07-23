// static/js/script.js
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('pdf-form');
    const previewContainer = document.getElementById('preview-container'); // Get the container, not the image
    const loadingSpinner = document.getElementById('loading-spinner');
    
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

    const updatePreview = () => {
        loadingSpinner.classList.remove('hidden');
        // Clear previous preview images
        previewContainer.innerHTML = ''; 
        previewContainer.appendChild(loadingSpinner); // Keep spinner inside

        const formData = new FormData(form);

        fetch('/preview', {
            method: 'POST',
            body: formData,
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw new Error(err.error) });
            }
            return response.json(); // We are now expecting a JSON response
        })
        .then(data => {
            // NEW: Handle the JSON response with multiple pages
            loadingSpinner.classList.add('hidden'); // Hide spinner first
            previewContainer.innerHTML = ''; // Clear container again to remove spinner
            
            if (data.pages && data.pages.length > 0) {
                // Loop through the array of page images
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
                previewContainer.textContent = 'No preview available. The generated PDF might be empty.';
            }
        })
        .catch(error => {
            console.error('Error fetching preview:', error);
            loadingSpinner.classList.add('hidden');
            previewContainer.innerHTML = `<p class="error-message">Error: ${error.message}</p>`;
        });
    };

    const debouncedUpdatePreview = debounce(updatePreview, 500);
    const inputs = form.querySelectorAll('.auto-update');
    inputs.forEach(input => {
        const eventType = (input.type === 'text' || input.type === 'number') ? 'input' : 'change';
        input.addEventListener(eventType, debouncedUpdatePreview);
    });
    
    // Initial preview on page load
    updatePreview();
});