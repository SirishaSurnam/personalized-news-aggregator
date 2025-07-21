document.addEventListener('DOMContentLoaded', function () {
    const bookmarkButtons = document.querySelectorAll('.bookmark-btn');

    bookmarkButtons.forEach(button => {
        button.addEventListener('click', function () {
            const articleId = this.dataset.articleId;
            const isBookmarked = this.dataset.bookmarked === 'true';
            const button = this;

            fetch('/toggle-bookmark/', { // Ensure this URL matches your Django URL
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': getCookie('csrftoken') // Function to get CSRF token
                },
                body: `article_id=${articleId}`
            })
                .then(response => response.json())
                .then(data => {
                    if (data.bookmarked !== undefined) {
                        button.dataset.bookmarked = data.bookmarked;
                        if (data.bookmarked) {
                            button.classList.remove('btn-outline-warning');
                            button.classList.add('btn-warning');
                            button.querySelector('.bookmark-text').textContent = 'Bookmarked';
                        } else {
                            button.classList.remove('btn-warning');
                            button.classList.add('btn-outline-warning');
                            button.querySelector('.bookmark-text').textContent = 'Bookmark';
                            // Optionally remove the card from bookmarks page
                            if (window.location.pathname.includes('/bookmarks')) {
                                button.closest('.card').remove();
                                // You might want to update pagination or show a message if all bookmarks are removed
                            }
                        }
                    }
                })
                .catch(error => console.error('Error toggling bookmark:', error));
        });
    });

    // Function to get CSRF token (required for Django POST requests)
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // News Refresh Button (on home.html)
    const refreshNewsButton = document.getElementById('refreshNews');
    if (refreshNewsButton) {
        refreshNewsButton.addEventListener('click', function () {
            this.textContent = 'Refreshing...';
            this.disabled = true;
            this.classList.remove('btn-success');
            this.classList.add('btn-info');

            fetch('/api/refresh-news/', { // Ensure this URL matches your Django API URL
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
                .then(response => response.json())
                .then(data => {
                    alert(data.message || 'News refresh initiated!');
                    // Optionally, you might want to reload the page after a delay or success
                    setTimeout(() => {
                        window.location.reload();
                    }, 2000); // Reload after 2 seconds
                })
                .catch(error => {
                    console.error('Error refreshing news:', error);
                    alert('Failed to refresh news. Check console for details.');
                    this.textContent = 'Refresh News';
                    this.disabled = false;
                    this.classList.remove('btn-info');
                    this.classList.add('btn-success');
                });
        });
    }
});


// static/js/main.js (Add loading states)
document.addEventListener('DOMContentLoaded', function () {
    const refreshButton = document.getElementById('refreshNews');
    if (refreshButton) {
        refreshButton.addEventListener('click', function () {
            this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Refreshing...';
            this.disabled = true;

            fetch('/api/refresh-news/')
                .then(response => response.json())
                .then(data => {
                    // Show toast notification instead of alert
                    showToast(data.message);
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                })
                .catch(error => {
                    showToast('Failed to refresh news', 'error');
                    this.innerHTML = '<i class="fas fa-sync-alt"></i> Refresh News';
                    this.disabled = false;
                });
        });
    }

    function showToast(message, type = 'success') {
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : 'success'} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');

        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;

        // Add to document
        document.body.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast, { delay: 3000 });
        bsToast.show();

        // Remove after hiding
        toast.addEventListener('hidden.bs.toast', function () {
            document.body.removeChild(toast);
        });
    }
});