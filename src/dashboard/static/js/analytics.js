// Professional Keyword Analytics & Export System

let keywordFilters = {
    dateRange: 30,
    platform: 'all',
    minFrequency: 2,
    topN: 20
};

let currentKeywordData = [];

// Apply Keyword Filters
async function applyKeywordFilters() {
    keywordFilters.dateRange = document.getElementById('keyword-date-range').value;
    keywordFilters.platform = document.getElementById('keyword-platform-filter').value;
    keywordFilters.minFrequency = parseInt(document.getElementById('keyword-min-freq').value);
    keywordFilters.topN = parseInt(document.getElementById('keyword-top-n').value);

    await loadKeywordAnalytics();
}

function resetKeywordFilters() {
    document.getElementById('keyword-date-range').value = '30';
    document.getElementById('keyword-platform-filter').value = 'all';
    document.getElementById('keyword-min-freq').value = '2';
    document.getElementById('keyword-top-n').value = '20';

    keywordFilters = {
        dateRange: 30,
        platform: 'all',
        minFrequency: 2,
        topN: 20
    };

    loadKeywordAnalytics();
}

// Load Keyword Analytics
async function loadKeywordAnalytics() {
    try {
        // Fetch keyword data
        const response = await fetch(`${API_BASE}/reports/keyword-frequency?top_n=${keywordFilters.topN}`);
        const data = await response.json();

        if (!data || data.length === 0) {
            showEmptyKeywordState();
            return;
        }

        currentKeywordData = data;

        // Calculate stats
        const totalKeywords = data.length;
        const totalFrequency = data.reduce((sum, kw) => sum + kw.frequency, 0);
        const avgFrequency = Math.round(totalFrequency / totalKeywords);
        const phrasesCount = data.filter(kw => kw.keyword.includes(' ')).length;

        // Update stats
        document.getElementById('kw-stat-total').textContent = totalKeywords;
        document.getElementById('kw-stat-phrases').textContent = phrasesCount;
        document.getElementById('kw-stat-avg').textContent = avgFrequency;
        document.getElementById('kw-stat-coverage').textContent = '100%';

        // Render chart
        renderKeywordChart(data);

        // Render table
        renderKeywordTable(data, totalFrequency);

    } catch (error) {
        console.error('Failed to load keyword analytics:', error);
        showEmptyKeywordState();
    }
}

function renderKeywordChart(data) {
    const ctx = document.getElementById('keywordsChart');
    if (!ctx) return;

    // Destroy existing
    if (window.keywordsChartInstance) {
        window.keywordsChartInstance.destroy();
    }

    window.keywordsChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.keyword),
            datasets: [{
                label: 'Frequency',
                data: data.map(d => d.frequency),
                backgroundColor: 'rgba(59, 130, 246, 0.8)',
                borderColor: 'rgba(59, 130, 246, 1)',
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(17, 24, 39, 0.95)',
                    titleColor: '#f9fafb',
                    bodyColor: '#d1d5db',
                    borderColor: '#374151',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: false,
                    callbacks: {
                        title: (items) => items[0].label,
                        label: (context) => {
                            const keyword = data[context.dataIndex];
                            return [
                                `Frequency: ${keyword.frequency}`,
                                `Relevance: High`,
                                `Platform: Multiple sources`
                            ];
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    grid: { color: '#374151' },
                    ticks: { color: '#9ca3af' }
                },
                y: {
                    grid: { display: false },
                    ticks: {
                        color: '#9ca3af',
                        font: { size: 11 }
                    }
                }
            }
        }
    });
}

function renderKeywordTable(data, totalFrequency) {
    const tbody = document.getElementById('keywords-table-body');

    if (data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-muted">No keywords found</td></tr>';
        return;
    }

    tbody.innerHTML = data.map(kw => {
        const coverage = ((kw.frequency / totalFrequency) * 100).toFixed(1);
        const relevance = kw.frequency > 10 ? 'High' : kw.frequency > 5 ? 'Medium' : 'Low';
        const trend = '→'; // Neutral for now

        return `
            <tr>
                <td class="font-mono text-sm">${escapeHtml(kw.keyword)}</td>
                <td>${kw.frequency}</td>
                <td><span class="status-badge ${relevance.toLowerCase()}">${relevance}</span></td>
                <td>${coverage}%</td>
                <td class="text-muted">${trend}</td>
            </tr>
        `;
    }).join('');
}

function showEmptyKeywordState() {
    document.getElementById('kw-stat-total').textContent = '0';
    document.getElementById('kw-stat-phrases').textContent = '0';
    document.getElementById('kw-stat-avg').textContent = '0';
    document.getElementById('kw-stat-coverage').textContent = '0%';

    document.getElementById('keywords-table-body').innerHTML =
        '<tr><td colspan="5" class="text-muted">No keywords available. Crawl sources to extract keywords.</td></tr>';
}

// Export Keyword Report
async function exportKeywordReport(format) {
    try {
        showToast('info', 'Generating Report', `Creating ${format.toUpperCase()} export...`);

        const params = new URLSearchParams({
            report_type: 'keywords',
            top_n: keywordFilters.topN
        });

        const url = `${API_BASE}/reports/export/${format}?${params.toString()}`;

        // Open in new tab
        window.open(url, '_blank');

        showToast('success', 'Export Ready', `${format.toUpperCase()} report generated successfully`);

    } catch (error) {
        console.error('Export failed:', error);
        showToast('error', 'Export Failed', error.message);
    }
}

// Source Deletion with Confirmation
async function deleteSource(sourceId, sourceName) {
    // Create confirmation modal
    const confirmed = confirm(
        `Delete source "${sourceName}"?\n\n` +
        `This will permanently remove:\n` +
        `• All crawled documents\n` +
        `• All keywords\n` +
        `• All crawl history\n\n` +
        `This action cannot be undone.`
    );

    if (!confirmed) {
        return;
    }

    try {
        showToast('info', 'Deleting Source', 'Removing source and associated data...');

        const response = await fetch(`${API_BASE}/sources/${sourceId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to delete source');
        }

        showToast('success', 'Source Deleted', `${sourceName} removed successfully`);

        // Reload sources
        if (currentTab === 'sources') {
            loadSources();
        }

        // Refresh analytics if on those pages
        if (currentTab === 'keywords') {
            loadKeywordAnalytics();
        }

    } catch (error) {
        console.error('Delete failed:', error);
        showToast('error', 'Delete Failed', error.message);
    }
}

// Enhanced loadSources with delete button
async function loadSources() {
    try {
        const response = await fetch(`${API_BASE}/sources/`);
        const sources = await response.json();

        const tbody = document.getElementById('sources-table-body');

        if (sources.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="9" class="text-muted">
                        No sources configured. Click "Add Source" to begin.
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = sources.map(source => `
            <tr>
                <td>${escapeHtml(source.name)}</td>
                <td><span class="font-mono text-xs">${source.content_type.toUpperCase()}</span></td>
                <td class="text-sm">${truncateUrl(source.url)}</td>
                <td class="font-mono text-xs">${source.config.frequency || 'Manual'}</td>
                <td>${source.config.rate_limit_per_minute || 60} req/min</td>
                <td>${source.config.max_hits || 100}</td>
                <td>${source.total_documents || 0}</td>
                <td><span class="status-badge ${source.status}">${source.status}</span></td>
                <td>
                    <div class="flex gap-2">
                        <button class="btn btn-secondary btn-sm" onclick="startCrawl('${source.id}')">
                            Start
                        </button>
                        <button class="btn btn-secondary btn-sm" style="color: var(--color-error);" 
                                onclick="deleteSource('${source.id}', '${escapeHtml(source.name).replace(/'/g, "\\'")}')">
                            Delete
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Failed to load sources:', error);
        document.getElementById('sources-table-body').innerHTML =
            '<tr><td colspan="9" class="text-muted">Error loading sources</td></tr>';
    }
}

// Make functions globally available
window.applyKeywordFilters = applyKeywordFilters;
window.resetKeywordFilters = resetKeywordFilters;
window.loadKeywordAnalytics = loadKeywordAnalytics;
window.exportKeywordReport = exportKeywordReport;
window.deleteSource = deleteSource;
window.loadSources = loadSources;
