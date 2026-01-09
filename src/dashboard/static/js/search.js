// Search Functionality
const searchBtn = document.getElementById('searchBtn');
const searchInput = document.getElementById('searchInput');
const searchResults = document.getElementById('searchResults');
const searchOperator = document.getElementById('searchOperator');
const searchContentType = document.getElementById('searchContentType');

// Search event listeners
searchBtn?.addEventListener('click', performSearch);

searchInput?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        performSearch();
    }
});

async function performSearch() {
    const query = searchInput.value.trim();

    if (!query) {
        searchResults.innerHTML = '<p class="text-muted">Please enter search keywords</p>';
        return;
    }

    searchResults.innerHTML = '<p class="text-muted">Searching...</p>';

    try {
        // Build query parameters
        const params = new URLSearchParams({
            q: query,
            operator: searchOperator.value,
            limit: 20
        });

        if (searchContentType.value) {
            params.append('content_type', searchContentType.value);
        }

        const response = await fetch(`${API_BASE}/search/?${params}`);
        const data = await response.json();

        renderSearchResults(data);
    } catch (error) {
        console.error('Search failed:', error);
        searchResults.innerHTML = '<p class="text-muted">Search failed. Please try again.</p>';
    }
}

function renderSearchResults(data) {
    if (!data.results || data.results.length === 0) {
        searchResults.innerHTML = `
            <p class="text-muted">
                No results found for "${escapeHtml(data.query)}". 
                Try different keywords or adjust your filters.
            </p>
        `;
        return;
    }

    searchResults.innerHTML = `
        <div style="margin-bottom: 1rem;">
            <p class="text-muted">Found ${data.total_results} results for "${escapeHtml(data.query)}"</p>
        </div>
        ${data.results.map(result => renderResultItem(result)).join('')}
    `;
}

function renderResultItem(result) {
    return `
        <div class="result-item">
            <div class="result-title">
                ${escapeHtml(result.title || 'Untitled Document')}
            </div>
            <div class="result-url">
                <a href="${escapeHtml(result.url)}" target="_blank" style="color: var(--text-muted);">
                    ${escapeHtml(result.url)}
                </a>
            </div>
            <div class="result-snippet">
                ${result.snippet}
            </div>
            <div style="margin-top: 0.5rem; font-size: 0.875rem; color: var(--text-muted);">
                <span class="status-badge status-idle">${result.content_type.toUpperCase()}</span>
                <span style="margin-left: 1rem;">Score: ${result.relevance_score.toFixed(2)}</span>
                <span style="margin-left: 1rem;">Crawled: ${formatDate(result.crawled_at)}</span>
            </div>
        </div>
    `;
}

// Clear search
function clearSearch() {
    searchInput.value = '';
    searchResults.innerHTML = '<p class="text-muted">Enter keywords to search documents</p>';
}
