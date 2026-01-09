// Professional Source Management System

class SourceManager {
    constructor() {
        this.modal = null;
        this.currentSourceType = 'website';
        this.init();
    }

    init() {
        this.createModal();
        this.attachEventListeners();
    }

    createModal() {
        const modalHTML = `
            <div class="modal-overlay" id="source-modal">
                <div class="modal">
                    <div class="modal-header">
                        <h2 class="modal-title">Add New Source</h2>
                        <p class="modal-subtitle">Configure a new crawl source</p>
                    </div>
                    <div class="modal-body">
                        <!-- Source Type Selection -->
                        <div class="form-section">
                            <div class="source-type-grid">
                                <div class="source-type-card selected" data-type="website">
                                    <div class="source-type-label">Website</div>
                                </div>
                                <div class="source-type-card" data-type="rss">
                                    <div class="source-type-label">RSS Feed</div>
                                </div>
                                <div class="source-type-card" data-type="twitter">
                                    <div class="source-type-label">Twitter/X</div>
                                </div>
                                <div class="source-type-card" data-type="reddit">
                                    <div class="source-type-label">Reddit</div>
                                </div>
                                <div class="source-type-card" data-type="youtube">
                                    <div class="source-type-label">YouTube</div>
                                </div>
                                <div class="source-type-card" data-type="linkedin">
                                    <div class="source-type-label">LinkedIn</div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Dynamic Form Container -->
                        <div id="source-form-container"></div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-secondary" onclick="sourceManager.closeModal()">Cancel</button>
                        <button class="btn btn-primary" onclick="sourceManager.submitSource()">
                            <span class="btn-text">Create Source</span>
                            <span class="loading" style="display: none;"></span>
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        this.modal = document.getElementById('source-modal');
    }

    attachEventListeners() {
        // Source type selection
        document.querySelectorAll('.source-type-card').forEach(card => {
            card.addEventListener('click', (e) => {
                document.querySelectorAll('.source-type-card').forEach(c => c.classList.remove('selected'));
                card.classList.add('selected');
                this.currentSourceType = card.dataset.type;
                this.renderForm();
            });
        });

        // Close on overlay click
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.closeModal();
            }
        });
    }

    openModal() {
        this.modal.classList.add('active');
        this.renderForm();
    }

    closeModal() {
        this.modal.classList.remove('active');
    }

    renderForm() {
        const container = document.getElementById('source-form-container');
        const forms = {
            website: this.getWebsiteForm(),
            rss: this.getRSSForm(),
            twitter: this.getTwitterForm(),
            reddit: this.getRedditForm(),
            youtube: this.getYouTubeForm(),
            linkedin: this.getLinkedInForm()
        };

        container.innerHTML = forms[this.currentSourceType];
    }

    getWebsiteForm() {
        return `
            <div class="form-section">
                <h3 class="form-section-title">Source Details</h3>
                <div class="form-group">
                    <label class="form-label">Source Name</label>
                    <input type="text" class="form-input" id="source-name" placeholder="e.g., Tech News Blog" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Website URL</label>
                    <input type="url" class="form-input" id="source-url" placeholder="https://example.com" required>
                    <p class="form-help">Full URL of the website to crawl</p>
                </div>
            </div>
            
            <div class="form-section">
                <h3 class="form-section-title">Crawl Configuration</h3>
                <div class="form-group">
                    <label class="form-label">Schedule (Cron)</label>
                    <input type="text" class="form-input" id="source-cron" value="0 0 * * *" required>
                    <p class="form-help">Cron expression: 0 0 * * * (daily at midnight)</p>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">Rate Limit (req/min)</label>
                        <input type="number" class="form-input" id="source-rate" value="30" min="1" max="300" required>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Max Pages</label>
                        <input type="number" class="form-input" id="source-max" value="100" min="1" max="10000" required>
                    </div>
                </div>
            </div>
        `;
    }

    getRSSForm() {
        return `
            <div class="form-section">
                <h3 class="form-section-title">Feed Details</h3>
                <div class="form-group">
                    <label class="form-label">Feed Name</label>
                    <input type="text" class="form-input" id="source-name" placeholder="e.g., News RSS Feed" required>
                </div>
                <div class="form-group">
                    <label class="form-label">RSS Feed URL</label>
                    <input type="url" class="form-input" id="source-url" placeholder="https://example.com/feed.xml" required>
                    <p class="form-help">URL to RSS/Atom feed</p>
                </div>
            </div>
            
            <div class="form-section">
                <h3 class="form-section-title">Crawl Configuration</h3>
                <div class="form-group">
                    <label class="form-label">Schedule (Cron)</label>
                    <input type="text" class="form-input" id="source-cron" value="0 */6 * * *" required>
                    <p class="form-help">Check feed every 6 hours</p>
                </div>
                <div class="form-group">
                    <label class="form-label">Max Items</label>
                    <input type="number" class="form-input" id="source-max" value="50" min="1" max="1000" required>
                </div>
            </div>
        `;
    }

    getTwitterForm() {
        return `
            <div class="form-section">
                <h3 class="form-section-title">Twitter Account</h3>
                <div class="form-group">
                    <label class="form-label">Account Name</label>
                    <input type="text" class="form-input" id="source-name" placeholder="e.g., TechCrunch Twitter" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Username or URL</label>
                    <input type="text" class="form-input" id="source-url" placeholder="@techcrunch or https://twitter.com/techcrunch" required>
                    <p class="form-help">Uses Nitter RSS (no API key needed)</p>
                </div>
            </div>
            
            <div class="form-section">
                <h3 class="form-section-title">Configuration</h3>
                <div class="form-group">
                    <label class="form-label">Schedule (Cron)</label>
                    <input type="text" class="form-input" id="source-cron" value="0 */4 * * *" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Max Tweets</label>
                    <input type="number" class="form-input" id="source-max" value="100" min="1" max="500" required>
                </div>
            </div>
        `;
    }

    getRedditForm() {
        return `
            <div class="form-section">
                <h3 class="form-section-title">Subreddit Details</h3>
                <div class="form-group">
                    <label class="form-label">Source Name</label>
                    <input type="text" class="form-input" id="source-name" placeholder="e.g., r/programming" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Subreddit</label>
                    <input type="text" class="form-input" id="source-url" placeholder="r/programming or https://reddit.com/r/programming" required>
                    <p class="form-help">Public subreddit only</p>
                </div>
            </div>
            
            <div class="form-section">
                <h3 class="form-section-title">Configuration</h3>
                <div class="form-group">
                    <label class="form-label">Schedule (Cron)</label>
                    <input type="text" class="form-input" id="source-cron" value="0 */6 * * *" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Max Posts</label>
                    <input type="number" class="form-input" id="source-max" value="50" min="1" max="500" required>
                </div>
            </div>
        `;
    }

    getYouTubeForm() {
        return `
            <div class="form-section">
                <h3 class="form-section-title">Channel Details</h3>
                <div class="form-group">
                    <label class="form-label">Channel Name</label>
                    <input type="text" class="form-input" id="source-name" placeholder="e.g., Tech Channel" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Channel/Playlist URL</label>
                    <input type="url" class="form-input" id="source-url" placeholder="https://youtube.com/channel/..." required>
                    <p class="form-help">Uses RSS feeds (no API key needed)</p>
                </div>
            </div>
            
            <div class="form-section">
                <h3 class="form-section-title">Configuration</h3>
                <div class="form-group">
                    <label class="form-label">Schedule (Cron)</label>
                    <input type="text" class="form-input" id="source-cron" value="0 0 * * *" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Max Videos</label>
                    <input type="number" class="form-input" id="source-max" value="30" min="1" max="200" required>
                </div>
            </div>
        `;
    }

    getLinkedInForm() {
        return `
            <div class="form-section">
                <h3 class="form-section-title">Company Page</h3>
                <div class="form-group">
                    <label class="form-label">Company Name</label>
                    <input type="text" class="form-input" id="source-name" placeholder="e.g., TechCorp LinkedIn" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Company Page URL</label>
                    <input type="url" class="form-input" id="source-url" placeholder="https://linkedin.com/company/techcorp" required>
                    <p class="form-help">Public company pages only (limited data)</p>
                </div>
            </div>
            
            <div class="form-section">
                <h3 class="form-section-title">Configuration</h3>
                <div class="form-group">
                    <label class="form-label">Schedule (Cron)</label>
                    <input type="text" class="form-input" id="source-cron" value="0 0 * * 1" required>
                    <p class="form-help">Weekly on Mondays</p>
                </div>
                <div class="form-group">
                    <label class="form-label">Max Posts</label>
                    <input type="number" class="form-input" id="source-max" value="20" min="1" max="100" required>
                </div>
            </div>
        `;
    }

    async submitSource() {
        const btn = document.querySelector('.modal-footer .btn-primary');
        const btnText = btn.querySelector('.btn-text');
        const loader = btn.querySelector('.loading');

        // Get form values
        const name = document.getElementById('source-name').value.trim();
        const url = document.getElementById('source-url').value.trim();
        const cron = document.getElementById('source-cron').value.trim();
        const rate = parseInt(document.getElementById('source-rate')?.value || '30');
        const maxHits = parseInt(document.getElementById('source-max').value);

        // Validation
        if (!name || !url) {
            showToast('error', 'Validation Error', 'Name and URL are required');
            return;
        }

        // Show loading
        btn.disabled = true;
        btnText.style.display = 'none';
        loader.style.display = 'inline-block';

        try {
            const payload = {
                name: name,
                url: url,
                source_type: this.getSourceTypeForAPI(),
                content_type: this.getContentTypeForAPI(),
                config: {
                    enabled: true,
                    frequency: cron,
                    rate_limit_per_minute: rate,
                    max_hits: maxHits,
                    follow_links: this.currentSourceType === 'website',
                    respect_robots: true,
                    retry_policy: {
                        max_retries: 3,
                        backoff_factor: 2,
                        timeout: 30
                    }
                }
            };

            const response = await fetch(`${API_BASE}/sources/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to create source');
            }

            const result = await response.json();
            showToast('success', 'Source Created', `${name} added successfully`);
            this.closeModal();

            // Reload sources table if on sources page
            if (currentTab === 'sources') {
                loadSources();
            }

        } catch (error) {
            showToast('error', 'Error', error.message);
        } finally {
            btn.disabled = false;
            btnText.style.display = 'inline';
            loader.style.display = 'none';
        }
    }

    getSourceTypeForAPI() {
        const mapping = {
            'website': 'website',
            'rss': 'rss_feed',
            'twitter': 'twitter',
            'reddit': 'reddit',
            'youtube': 'youtube',
            'linkedin': 'linkedin'
        };
        return mapping[this.currentSourceType];
    }

    getContentTypeForAPI() {
        const mapping = {
            'website': 'html',
            'rss': 'rss',
            'twitter': 'twitter',
            'reddit': 'reddit',
            'youtube': 'youtube',
            'linkedin': 'linkedin'
        };
        return mapping[this.currentSourceType];
    }
}

// Initialize
const sourceManager = new SourceManager();

// Toast notification system
function showToast(type, title, message) {
    const container = document.querySelector('.toast-container') || createToastContainer();

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <div class="toast-title">${title}</div>
        <div class="toast-message">${message}</div>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'toast-slide-out 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
    return container;
}
