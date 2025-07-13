// JavaScript for AI News Digest Generator
document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const statusElement = document.getElementById('progress-message');
    const progressBar = document.querySelector('.progress-fill');
    const generateButton = document.querySelector('.btn-primary');
    
    // Status polling
    let statusInterval;
    
    // Check if report is currently running
    if (generateButton && generateButton.disabled) {
        startStatusPolling();
    }
    
    // Start polling for status updates
    function startStatusPolling() {
        statusInterval = setInterval(function() {
            fetch('/status')
                .then(response => response.json())
                .then(data => {
                    updateStatus(data);
                    
                    // Stop polling when report is complete
                    if (!data.running) {
                        clearInterval(statusInterval);
                        
                        // Refresh page after a short delay to show updated reports
                        setTimeout(() => {
                            window.location.reload();
                        }, 2000);
                    }
                })
                .catch(error => {
                    console.error('Error fetching status:', error);
                });
        }, 2000); // Poll every 2 seconds
    }
    
    // Update status display
    function updateStatus(status) {
        if (statusElement) {
            statusElement.textContent = status.progress || 'Processing...';
        }
        
        if (progressBar) {
            if (status.running) {
                progressBar.classList.add('animate');
            } else {
                progressBar.classList.remove('animate');
            }
        }
        
        if (generateButton) {
            generateButton.disabled = status.running;
            
            if (status.running) {
                generateButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating Report...';
            } else {
                generateButton.innerHTML = '<i class="fas fa-play"></i> Generate Report';
            }
        }
    }
    
    // Auto-hide flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            setTimeout(() => {
                message.remove();
            }, 300);
        }, 5000);
    });
    
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });
    
    // Add loading state to download buttons
    const downloadButtons = document.querySelectorAll('a[href*="/download/"]');
    downloadButtons.forEach(button => {
        button.addEventListener('click', function() {
            const originalText = this.innerHTML;
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Downloading...';
            this.style.pointerEvents = 'none';
            
            // Reset button after 3 seconds
            setTimeout(() => {
                this.innerHTML = originalText;
                this.style.pointerEvents = 'auto';
            }, 3000);
        });
    });
    
    // Add confirmation for delete buttons
    const deleteButtons = document.querySelectorAll('a[href*="/delete/"]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const filename = this.href.split('/').pop();
            const confirmMessage = `Are you sure you want to delete the report "${filename}"?`;
            
            if (confirm(confirmMessage)) {
                // Add loading state
                this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deleting...';
                this.style.pointerEvents = 'none';
                
                // Navigate to delete URL
                window.location.href = this.href;
            }
        });
    });
    
    // Add tooltips to buttons
    const tooltips = {
        'download': 'Download this report as PDF',
        'delete': 'Delete this report permanently',
        'generate': 'Generate a new AI news digest report'
    };
    
    Object.keys(tooltips).forEach(key => {
        const elements = document.querySelectorAll(`[data-tooltip="${key}"]`);
        elements.forEach(element => {
            element.title = tooltips[key];
        });
    });
    
    // Add keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + G to generate report
        if ((e.ctrlKey || e.metaKey) && e.key === 'g') {
            e.preventDefault();
            if (generateButton && !generateButton.disabled) {
                generateButton.click();
            }
        }
        
        // Escape to close any modal/overlay (future use)
        if (e.key === 'Escape') {
            // Handle escape key
        }
    });
    
    // Add visual feedback for form submission
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitButton = this.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.disabled = true;
                const originalText = submitButton.innerHTML;
                submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
                
                // Re-enable after 5 seconds (fallback)
                setTimeout(() => {
                    submitButton.disabled = false;
                    submitButton.innerHTML = originalText;
                }, 5000);
            }
        });
    });
    
    // Add table row highlighting
    const tableRows = document.querySelectorAll('tbody tr');
    tableRows.forEach(row => {
        row.addEventListener('mouseenter', function() {
            this.style.backgroundColor = '#f8f9fa';
        });
        
        row.addEventListener('mouseleave', function() {
            if (!this.classList.contains('highlight')) {
                this.style.backgroundColor = '';
            }
        });
    });
    
    // Add copy to clipboard functionality (future enhancement)
    function copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
            showNotification('Copied to clipboard!', 'success');
        }).catch(err => {
            console.error('Could not copy text: ', err);
            showNotification('Failed to copy to clipboard', 'error');
        });
    }
    
    // Show notification (future enhancement)
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'success' ? '#27ae60' : type === 'error' ? '#e74c3c' : '#3498db'};
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            z-index: 1000;
            opacity: 0;
            transform: translateY(-20px);
            transition: all 0.3s ease;
        `;
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateY(0)';
        }, 100);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateY(-20px)';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }
    
    // Add performance monitoring
    const performanceObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
            if (entry.entryType === 'navigation') {
                console.log('Page load time:', entry.loadEventEnd - entry.loadEventStart, 'ms');
            }
        }
    });
    
    try {
        performanceObserver.observe({entryTypes: ['navigation']});
    } catch (e) {
        // Performance Observer not supported
    }
    
    // Add error handling for AJAX requests
    window.addEventListener('error', function(e) {
        console.error('JavaScript error:', e.error);
        showNotification('An error occurred. Please refresh the page.', 'error');
    });
    
    // Add window beforeunload handler for report generation
    window.addEventListener('beforeunload', function(e) {
        if (generateButton && generateButton.disabled) {
            e.preventDefault();
            e.returnValue = 'Report generation is in progress. Are you sure you want to leave?';
        }
    });
    
    console.log('AI News Digest Generator initialized');
}); 