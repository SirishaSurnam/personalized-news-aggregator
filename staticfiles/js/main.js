function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

document.addEventListener('DOMContentLoaded', function () {
    const bookmarkButtons = document.querySelectorAll('.bookmark-btn');

    bookmarkButtons.forEach(button => {
        button.addEventListener('click', function () {
            const articleId = this.dataset.articleId;
            const button = this;

            fetch('/toggle-bookmark/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': getCookie('csrftoken')
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
                            if (window.location.pathname.includes('/bookmarks')) {
                                button.closest('.card').remove();
                            }
                        }
                    }
                })
                .catch(error => console.error('Error toggling bookmark:', error));
        });
    });

    // 🔽 Summary form
    document.body.addEventListener('submit', function (e) {
        if (e.target.classList.contains('summary-form')) {
            e.preventDefault();
            const form = e.target;
            const articleId = form.dataset.articleId;

            fetch('/fetch-summary-single/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `article_id=${articleId}`
            }).then(() => {
                form.innerHTML = "<small>Fetching summary...</small>";
            });
        }
    });

    // Refresh button logic
    const refreshNewsButton = document.getElementById('refreshNews');
    if (refreshNewsButton) {
        refreshNewsButton.addEventListener('click', function () {
            this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Refreshing...';
            this.disabled = true;

            fetch('/api/refresh-news/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
                .then(response => response.json())
                .then(data => {
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

        document.body.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast, { delay: 3000 });
        bsToast.show();
        toast.addEventListener('hidden.bs.toast', function () {
            document.body.removeChild(toast);
        });
    }
});