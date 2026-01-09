// Professional App Logic - Web Analytics Platform

// Navigation
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', (e) => {
        e.preventDefault();
        const page = e.target.dataset.page;
        switchPage(page);
    });
});

function switchPage(page) {
    // Update nav
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.page === page) {
            item.classList.add('active');
        }
    });

    // Update content
    document.querySelectorAll('.page-section').forEach(section => {
        section.classList.remove('active');
    });
    document.getElementById(`${page}-page`).classList.add('active');

    currentTab = page;

    // Load page data
    loadPageData(page);
}

function loadPageData(page) {
    switch (page) {
        case 'overview':
            loadOverviewStats();
            loadOverviewCharts();
            break;
        case 'sources':
            loadSources();
            break;
        case 'analytics':
            loadCharts();
            break;
        case 'keywords':
            loadKeywordsChart();
            break;
        case 'blocking':
            loadBlockingStats();
            break;
        case 'reports':
            loadTimelineChart();
            break;
        case 'decision':
            refreshDecisionSummary();
            loadSignalRadar();
            loadConceptClusters();
            break;
    }
}

// Overview Page
async function loadOverviewStats() {
    try {
        const statsResponse = await fetch(`${API_BASE}/crawler/stats`);
        const stats = await statsResponse.json();

        document.getElementById('stat-total-sources').textContent = stats.total_sources || 0;
        document.getElementById('stat-total-documents').textContent

            = stats.total_documents || 0;
        document.getElementById('stat-active-crawls').textContent = stats.active_crawls || 0;
        document.getElementById('stat-blocked-sources').textContent = stats.blocked_sources || 0;
    } catch (error) {
        console.error('Failed to load overview stats:', error);
    }
}

async function loadOverviewCharts() {
    // Timeline
    try {
        const response = await fetch(`${API_BASE}/reports/crawl-timeline?days=30`);
        const data = await response.json();

        const ctx = document.getElementById('overviewTimelineChart');
        if (ctx) {
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.map(d => new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })),
                    datasets: [{
                        label: 'Documents',
                        data: data.map(d => d.documents_collected),
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.3
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: { color: '#374151' },
                            ticks: { color: '#9ca3af' }
                        },
                        x: {
                            grid: { display: false },
                            ticks: { color: '#9ca3af' }
                        }
                    }
                }
            });
        }
    } catch (error) {
        console.error('Failed to load timeline:', error);
    }

    // Health chart
    try {
        const response = await fetch(`${API_BASE}/reports/blocking-stats`);
        const data = await response.json();

        const ctx = document.getElementById('overviewHealthChart');
        if (ctx) {
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Healthy', 'Blocked', 'Running', 'Failed'],
                    datasets: [{
                        data: [data.healthy, data.blocked, data.running, data.failed],
                        backgroundColor: ['#10b981', '#ef4444', '#3b82f6', '#f59e0b'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: { color: '#9ca3af', padding: 15 }
                        }
                    }
                }
            });
        }
    } catch (error) {
        console.error('Failed to load health chart:', error);
    }
}

// Sources Page - Logic moved to analytics.js
// async function loadSources() { ... }

async function startCrawl(sourceId) {
    try {
        await fetch(`${API_BASE}/crawler/start/${sourceId}`, { method: 'POST' });
        setTimeout(() => loadSources(), 1000);
    } catch (error) {
        console.error('Failed to start crawl:', error);
    }
}

// Blocking Page
async function loadBlockingStats() {
    try {
        const response = await fetch(`${API_BASE}/reports/blocking-stats`);
        const data = await response.json();

        document.getElementById('blocking-stat-blocked').textContent = data.blocked || 0;
        document.getElementById('blocking-stat-http').textContent = data.blocked || 0;
        document.getElementById('blocking-stat-robots').textContent = 0;

        const tbody = document.getElementById('blocked-sources-table');

        if (!data.blocked_sources || data.blocked_sources.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="text-muted">No blocked sources</td></tr>';
            return;
        }

        tbody.innerHTML = data.blocked_sources.map(source => `
            <tr>
                <td>${escapeHtml(source.name)}</td>
                <td><span class="font-mono text-xs">${source.content_type.toUpperCase()}</span></td>
                <td>${escapeHtml(source.error)}</td>
                <td class="text-muted text-xs">Just now</td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Failed to load blocking stats:', error);
    }
}

// Reports
async function exportReport(type, format) {
    try {
        const url = `${API_BASE}/reports/export/${format}?report_type=${type}`;
        window.open(url, '_blank');
    } catch (error) {
        console.error('Failed to export report:', error);
    }
}

// Utilities
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function truncateUrl(url, maxLength = 40) {
    if (url.length <= maxLength) return url;
    return url.substring(0, maxLength - 3) + '...';
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadProjects();  // Load projects first
    loadOverviewStats();
    loadOverviewCharts();

    // Auto-refresh stats every 30 seconds
    setInterval(() => {
        if (currentTab === 'overview') {
            loadOverviewStats();
        }
    }, 30000);
});
