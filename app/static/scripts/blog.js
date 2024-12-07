const blogManager = {
    currentPage: 1,
    pageSize: 10,
    isLoading: false,
    hasMorePosts: true,

    init() {
        this.loadMoreBtn = document.getElementById('loadMoreBtn');
        this.blogGrid = document.getElementById('blogGrid');
        this.baseUrl = document.querySelector('meta[name="base-url"]').content;
        
        // Hide load more button if no more posts
        if (!this.hasMorePosts) {
            this.loadMoreBtn.style.display = 'none';
        }
    },

    async loadMorePosts() {
        if (this.isLoading || !this.hasMorePosts) return;

        try {
            this.isLoading = true;
            this.loadMoreBtn.textContent = 'Loading...';

            const response = await fetch(
                `${this.baseUrl}/api/blog?page=${this.currentPage}&limit=${this.pageSize}`
            );
            
            if (!response.ok) throw new Error('Failed to fetch posts');
            
            const data = await response.json();
            
            if (data.posts.length < this.pageSize) {
                this.hasMorePosts = false;
                this.loadMoreBtn.style.display = 'none';
            }

            this.appendPosts(data.posts);
            this.currentPage++;

        } catch (error) {
            console.error('Error loading posts:', error);
            this.loadMoreBtn.textContent = 'Error loading posts. Try again.';
        } finally {
            this.isLoading = false;
            if (this.hasMorePosts) {
                this.loadMoreBtn.textContent = 'Load More';
            }
        }
    },

    createPostElement(post) {
        const postUrl = `${this.baseUrl}/api/blog/${post.id}`;
        return `
            <div class="blog-card" data-post-id="${post.id}">
                <div class="blog-image">
                    <img src="${post.image_url || '/api/placeholder/400/300'}" alt="${post.title}">
                </div>
                <div class="blog-content">
                    <h2 class="blog-title">${post.title}</h2>
                    <div class="blog-meta">
                        <span class="blog-date">${new Date(post.created_at).toLocaleDateString()}</span>
                    </div>
                    <div class="blog-summary">
                        <p>${post.content.slice(0, 150)}...</p>
                    </div>
                    <div class="blog-actions">
                        <a href="${postUrl}" class="blog-action read-more">Read More</a>
                        <a href="#" class="blog-action share-linkedin" onclick="blogManager.sharePost('${post.id}')">Share on LinkedIn</a>
                    </div>
                </div>
            </div>
        `;
    },

    appendPosts(posts) {
        posts.forEach(post => {
            const postElement = this.createPostElement(post);
            this.blogGrid.insertAdjacentHTML('beforeend', postElement);
        });
    },

    async sharePost(postId) {
        try {
            const post = await this.getPostDetails(postId);
            const shareUrl = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(
                `${this.baseUrl}/api/blog/${postId}`
            )}&title=${encodeURIComponent(post.title)}`;
            window.open(shareUrl, '_blank', 'width=600,height=600');
        } catch (error) {
            console.error('Error sharing post:', error);
        }
    },

    async getPostDetails(postId) {
        const response = await fetch(`${this.baseUrl}/api/blog/${postId}`);
        if (!response.ok) throw new Error('Failed to fetch post details');
        return await response.json();
    }
};

const blogPostManager = {
    init() {
        try {
            // Check if we're on a blog post page by looking for necessary elements
            const metaBaseUrl = document.querySelector('meta[name="base-url"]');
            const metaPostId = document.querySelector('meta[name="post-id"]');
            const likeButton = document.getElementById('likeButton');
            const likeCount = document.getElementById('likeCount');

            // Only initialize if we're on a blog post page
            if (metaBaseUrl && metaPostId && likeButton && likeCount) {
                this.baseUrl = metaBaseUrl.content;
                this.postId = metaPostId.content;
                this.likeButton = likeButton;
                this.likeCount = likeCount;
                this.setupEventListeners();
                this.checkInitialLikeStatus();
                console.log('Blog post manager initialized successfully');
            } else {
                console.log('Not a blog post page, skipping initialization');
                return;
            }
        } catch (error) {
            console.error('Error initializing blog post manager:', error);
        }
    },

    setupEventListeners() {
        if (this.likeButton) {
            this.likeButton.addEventListener('click', () => this.handleLikeClick());
        }
    },

    async handleLikeClick() {
        try {
            const email = await this.getUserEmail();
            if (!email) return;

            const isLiked = this.likeButton.getAttribute('aria-pressed') === 'true';
            const method = isLiked ? 'DELETE' : 'POST';
            
            const response = await fetch(`${this.baseUrl}/api/blog/${this.postId}/like?user_email=${encodeURIComponent(email)}`, {
                method: method,
                headers: {
                  'Content-Type': 'application/json',
                },
                body: JSON.stringify({ post_id: parseInt(this.postId) }),
              });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to process like action');
            }

            // Update UI
            await this.updateLikeStatus();
            this.showToast(isLiked ? 'Post unliked' : 'Post liked', 'success');
            
        } catch (error) {
            console.error('Error:', error);
            this.showToast(error.message, 'error');
        }
    },

    async getUserEmail() {
        let email = localStorage.getItem('userEmail');
        
        if (!email) {
            const emailInput = await this.showEmailPrompt();
            if (!emailInput) return null;
            
            if (this.validateEmail(emailInput)) {
                localStorage.setItem('userEmail', emailInput);
                return emailInput;
            } else {
                this.showToast('Please enter a valid email address', 'error');
                return null;
            }
        }
        return email;
    },

    async updateLikeStatus() {
        try {
            // Get updated like count
            const countResponse = await fetch(`${this.baseUrl}/api/blog/${this.postId}/likes/count`);
            if (!countResponse.ok) {
                throw new Error('Failed to fetch like count');
            }
            const { likes_count } = await countResponse.json();
            this.likeCount.textContent = likes_count;

            // Check if current user has liked
            const email = localStorage.getItem('userEmail');
            if (email) {
                //const statusResponse = await fetch(`${this.baseUrl}/api/blog/${this.postId}/likes/status?user_email=${encodeURIComponent(email)}`);
                const statusResponse = await fetch(`${this.baseUrl}/api/blog/${this.postId}/like-status?user_email=${encodeURIComponent(email)}`);
                if (!statusResponse.ok) {
                    throw new Error('Failed to fetch like status');
                }
                const { is_liked } = await statusResponse.json();
                this.likeButton.setAttribute('aria-pressed', is_liked);
                this.likeButton.classList.toggle('liked', is_liked);
            }

            // Update recent likes
            await this.updateRecentLikes();
        } catch (error) {
            console.error('Error updating like status:', error);
            this.showToast('Failed to update like status', 'error');
        }
    },

    async updateRecentLikes() {
        const recentLikersElement = document.querySelector('.recent-likers');
        if (!recentLikersElement) return;

        try {
            const response = await fetch(`${this.baseUrl}/api/blog/${this.postId}/likes/details?limit=5`);
            if (!response.ok) {
                throw new Error('Failed to fetch recent likes');
            }
            
            const { likes } = await response.json();
            if (likes && likes.length > 0) {
                recentLikersElement.innerHTML = likes
                  .map(
                    (like) => `
                      <span title="${like.user_email}">
                        ${like.user_email.split('@')[0]}
                      </span>
                    `
                  )
                  .join('');
              } else {
                recentLikersElement.innerHTML = '<span>No likes yet</span>';
              }
        } catch (error) {
            console.error('Error updating recent likes:', error);
            recentLikersElement.innerHTML = '<span>Failed to load recent likes</span>';
        }
    },

    async checkInitialLikeStatus() {
        if (this.postId) {
            await this.updateLikeStatus();
        }
    },

    showEmailPrompt() {
        return new Promise((resolve) => {
            const modalHtml = `
                <div id="emailPromptModal" class="emodal">
                    <div class="emodal-content">
                        <h3>Enter Your Email</h3>
                        <p>Please enter your email to like this post:</p>
                        <input type="email" id="promptEmailInput" placeholder="your@email.com" required>
                        <div class="emodal-buttons">
                            <button id="cancelEmailButton">Cancel</button>
                            <button id="submitEmailButton">Submit</button>
                        </div>
                    </div>
                </div>
            `;

            document.body.insertAdjacentHTML('beforeend', modalHtml);

            const modal = document.getElementById('emailPromptModal');
            const emailInput = document.getElementById('promptEmailInput');
            const submitButton = document.getElementById('submitEmailButton');
            const cancelButton = document.getElementById('cancelEmailButton');

            modal.style.display = 'block';

            submitButton.addEventListener('click', () => {
                const email = emailInput.value.trim();
                modal.remove();
                resolve(email);
            });

            cancelButton.addEventListener('click', () => {
                modal.remove();
                resolve(null);
            });

            emailInput.addEventListener('keyup', (event) => {
                if (event.key === 'Enter') {
                    const email = emailInput.value.trim();
                    modal.remove();
                    resolve(email);
                }
            });
        });
    },

    validateEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    },

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);
        setTimeout(() => {
            toast.classList.add('fade-out');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
};

// Initialize blog manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    blogManager.init();
    blogPostManager.init();
});


