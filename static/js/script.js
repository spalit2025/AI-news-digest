// Enhanced AI News Digest Generator - JavaScript
// Handles progress polling and source selection

let progressInterval;
let isGenerating = false;

// Default sources for "Select Default" button
const defaultSources = ['OpenAI', 'Hugging Face', 'DeepMind', 'Anthropic', 'VentureBeat AI'];

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    initializeSourceSelection();
    initializeProgressPolling();
    updateSelectedCount();
});

// Source Selection Functions
function initializeSourceSelection() {
    const selectAllBtn = document.getElementById('selectAll');
    const selectNoneBtn = document.getElementById('selectNone');
    const selectDefaultBtn = document.getElementById('selectDefault');
    const sourceForm = document.getElementById('sourceForm');
    const sourceInputs = document.querySelectorAll('.source-input');

    // Add event listeners for control buttons
    if (selectAllBtn) {
        selectAllBtn.addEventListener('click', function() {
            sourceInputs.forEach(input => {
                input.checked = true;
            });
            updateSelectedCount();
        });
    }

    if (selectNoneBtn) {
        selectNoneBtn.addEventListener('click', function() {
            sourceInputs.forEach(input => {
                input.checked = false;
            });
            updateSelectedCount();
        });
    }

    if (selectDefaultBtn) {
        selectDefaultBtn.addEventListener('click', function() {
            // First uncheck all
            sourceInputs.forEach(input => {
                input.checked = false;
            });
            
            // Then check default sources
            sourceInputs.forEach(input => {
                if (defaultSources.includes(input.value)) {
                    input.checked = true;
                }
            });
            updateSelectedCount();
        });
    }

    // Add event listeners for individual checkboxes
    sourceInputs.forEach(input => {
        input.addEventListener('change', function() {
            updateSelectedCount();
        });
    });

    // Add form validation
    if (sourceForm) {
        sourceForm.addEventListener('submit', function(e) {
            const selectedSources = document.querySelectorAll('.source-input:checked');
            
            if (selectedSources.length === 0) {
                e.preventDefault();
                alert('Please select at least one source to generate a report.');
                return false;
            }
            
            // Show loading state
            const submitBtn = sourceForm.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Starting...';
            }
            
            return true;
        });
    }
}

// Update the count of selected sources
function updateSelectedCount() {
    const selectedSources = document.querySelectorAll('.source-input:checked');
    const countElement = document.getElementById('selectedCount');
    
    if (countElement) {
        countElement.textContent = selectedSources.length;
    }
    
    // Update generate button state
    const generateBtn = document.querySelector('button[type="submit"]');
    if (generateBtn && !isGenerating) {
        if (selectedSources.length === 0) {
            generateBtn.disabled = true;
            generateBtn.innerHTML = '<i class="fas fa-play"></i> Select Sources First';
        } else {
            generateBtn.disabled = false;
            generateBtn.innerHTML = '<i class="fas fa-play"></i> Generate Report';
        }
    }
}

// Progress Polling Functions
function initializeProgressPolling() {
    // Check if we should start polling immediately
    checkInitialStatus();
    
    // Set up periodic status checks
    setInterval(checkStatus, 3000); // Check every 3 seconds
}

function checkInitialStatus() {
    fetch('/status')
        .then(response => response.json())
        .then(data => {
            if (data.running) {
                startProgressPolling();
            }
            updateProgress(data);
        })
        .catch(error => {
            console.error('Error checking status:', error);
        });
}

function startProgressPolling() {
    if (progressInterval) return; // Already polling
    
    isGenerating = true;
    updateGenerateButton(true);
    
    progressInterval = setInterval(() => {
        fetch('/status')
            .then(response => response.json())
            .then(data => {
                updateProgress(data);
                
                if (!data.running) {
                    stopProgressPolling();
                    
                    // Refresh the page after a short delay to show new reports
                    setTimeout(() => {
                        window.location.reload();
                    }, 2000);
                }
            })
            .catch(error => {
                console.error('Error polling progress:', error);
                stopProgressPolling();
            });
    }, 2000); // Poll every 2 seconds
}

function stopProgressPolling() {
    if (progressInterval) {
        clearInterval(progressInterval);
        progressInterval = null;
    }
    
    isGenerating = false;
    updateGenerateButton(false);
}

function updateProgress(data) {
    const progressMessage = document.getElementById('progress-message');
    const progressSection = document.querySelector('.progress-section');
    const progressFill = document.querySelector('.progress-fill');
    
    if (progressMessage && data.progress) {
        progressMessage.textContent = data.progress;
    }
    
    if (progressSection) {
        progressSection.style.display = data.running || data.progress ? 'block' : 'none';
    }
    
    if (progressFill) {
        if (data.running) {
            progressFill.classList.add('animate');
        } else {
            progressFill.classList.remove('animate');
        }
    }
    
    // Update error display
    const errorMessage = document.querySelector('.error-message');
    if (errorMessage) {
        if (data.error) {
            errorMessage.style.display = 'block';
            errorMessage.innerHTML = `<i class="fas fa-exclamation-triangle"></i> Error: ${data.error}`;
        } else {
            errorMessage.style.display = 'none';
        }
    }
}

function updateGenerateButton(isRunning) {
    const generateBtn = document.querySelector('button[type="submit"]');
    if (!generateBtn) return;
    
    if (isRunning) {
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating Report...';
    } else {
        const selectedSources = document.querySelectorAll('.source-input:checked');
        if (selectedSources.length === 0) {
            generateBtn.disabled = true;
            generateBtn.innerHTML = '<i class="fas fa-play"></i> Select Sources First';
        } else {
            generateBtn.disabled = false;
            generateBtn.innerHTML = '<i class="fas fa-play"></i> Generate Report';
        }
    }
}

function checkStatus() {
    // Light status check without updating UI (just to sync state)
    fetch('/status')
        .then(response => response.json())
        .then(data => {
            if (data.running && !isGenerating) {
                startProgressPolling();
            } else if (!data.running && isGenerating) {
                stopProgressPolling();
            }
        })
        .catch(error => {
            console.error('Error checking status:', error);
        });
}

// Flash message auto-hide (optional enhancement)
document.addEventListener('DOMContentLoaded', function() {
    const flashMessages = document.querySelectorAll('.flash-message');
    
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            setTimeout(() => {
                message.remove();
            }, 500);
        }, 5000); // Hide after 5 seconds
    });
});

// Add some visual feedback for source selection
document.addEventListener('DOMContentLoaded', function() {
    const sourceItems = document.querySelectorAll('.source-item');
    
    sourceItems.forEach(item => {
        const checkbox = item.querySelector('.source-input');
        const label = item.querySelector('.source-checkbox');
        
        if (checkbox && label) {
            checkbox.addEventListener('change', function() {
                if (this.checked) {
                    item.classList.add('selected');
                } else {
                    item.classList.remove('selected');
                }
            });
            
            // Set initial state
            if (checkbox.checked) {
                item.classList.add('selected');
            }
        }
    });
}); 