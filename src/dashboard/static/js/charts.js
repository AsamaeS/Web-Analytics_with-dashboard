// Enhanced Charts for Analytics Dashboard with Real Data
let chartsLoaded = false;
let chartsMap = {};

// Initialize charts when analytics tab is active
function loadCharts() {
    if (chartsLoaded) {
        refreshCharts();
        return;
    }

    loadDocumentsChart();
    loadTimelineChart();
    loadKeywordsChart();
    loadPlatformComparisonChart();
    loadContentTypeChart();
    loadRadarChart();

    chartsLoaded = true;

    // Auto-refresh every 2 minutes
    setInterval(() => {
        if (currentTab === 'analytics') {
            refreshCharts();
        }
    }, 120000);
}

function refreshCharts() {
    loadDocumentsChart();
    loadTimelineChart();
    loadKeywordsChart();
    loadPlatformComparisonChart();
    loadContentTypeChart();
}

// Documents per Source Chart
async function loadDocumentsChart() {
    try {
        const response = await fetch(`${API_BASE}/reports/source-summary`);
        const data = await response.json();

        // Default to empty if no data
        if (!data || data.length === 0) {
            data = [{ source_name: 'No Data', document_count: 0 }];
        }

        const ctx = document.getElementById('documentsChart');
        if (!ctx) return;

        // Destroy existing chart
        if (chartsMap.documents) {
            chartsMap.documents.destroy();
        }

        chartsMap.documents = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(d => d.source_name),
                datasets: [{
                    label: 'Documents',
                    data: data.map(d => d.document_count),
                    backgroundColor: 'rgba(59, 130, 246, 0.8)', // Secondary
                    borderColor: 'rgba(59, 130, 246, 1)',
                    borderWidth: 1
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
                        ticks: { color: '#94a3b8' },
                        grid: { color: 'rgba(148, 163, 184, 0.1)' }
                    },
                    x: {
                        ticks: {
                            color: '#94a3b8',
                            maxRotation: 45,
                            minRotation: 45
                        },
                        grid: { display: false }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Failed to load documents chart:', error);
    }
}

// Crawl Activity Timeline Chart
async function loadTimelineChart() {
    try {
        const response = await fetch(`${API_BASE}/reports/crawl-timeline?days=30`);
        const data = await response.json();

        // Default empty state
        if (!data || data.length === 0) {
            data = [{ date: new Date().toISOString(), crawl_count: 0, documents_collected: 0 }];
        }

        const ctx = document.getElementById('timelineChart');
        if (!ctx) return;

        if (chartsMap.timeline) {
            chartsMap.timeline.destroy();
        }

        chartsMap.timeline = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.map(d => new Date(d.date).toLocaleDateString()),
                datasets: [{
                    label: 'Crawls',
                    data: data.map(d => d.crawl_count),
                    borderColor: 'rgba(16, 185, 129, 1)', // Success
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    fill: true,
                    tension: 0.4
                }, {
                    label: 'Documents',
                    data: data.map(d => d.documents_collected),
                    borderColor: 'rgba(6, 182, 212, 1)', // Accent
                    backgroundColor: 'rgba(6, 182, 212, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        labels: { color: '#94a3b8' }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { color: '#94a3b8' },
                        grid: { color: 'rgba(148, 163, 184, 0.1)' }
                    },
                    x: {
                        ticks: { color: '#94a3b8' },
                        grid: { display: false }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Failed to load timeline chart:', error);
    }
}

// Top Keywords Chart
async function loadKeywordsChart() {
    try {
        const response = await fetch(`${API_BASE}/reports/keyword-frequency?top_n=15`);
        const data = await response.json();

        if (!data || data.length === 0) {
            console.log('No keyword data available');
            return;
        }

        const ctx = document.getElementById('keywordsChart');
        if (!ctx) return;

        if (chartsMap.keywords) {
            chartsMap.keywords.destroy();
        }

        chartsMap.keywords = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(d => d.keyword),
                datasets: [{
                    label: 'Frequency',
                    data: data.map(d => d.frequency),
                    backgroundColor: 'rgba(245, 158, 11, 0.8)',
                    borderColor: 'rgba(245, 158, 11, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: { color: '#94a3b8' },
                        grid: { color: 'rgba(148, 163, 184, 0.1)' }
                    },
                    y: {
                        ticks: { color: '#94a3b8' },
                        grid: { display: false }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Failed to load keywords chart:', error);
    }
}

// Platform Comparison Chart
async function loadPlatformComparisonChart() {
    try {
        const response = await fetch(`${API_BASE}/reports/content-type-distribution`);
        const data = await response.json();

        // Default empty state
        if (!data || data.length === 0) {
            data = [{ content_type: 'No Data', count: 1 }];
        }

        const colors = {
            'html': 'rgba(11, 90, 142, 0.8)',   // Primary
            'rss': 'rgba(59, 130, 246, 0.8)',    // Secondary
            'pdf': 'rgba(6, 182, 212, 0.8)',     // Accent
            'txt': 'rgba(16, 185, 129, 0.8)',    // Success
            'twitter': 'rgba(29, 161, 242, 0.8)',
            'reddit': 'rgba(255, 69, 0, 0.8)',
            'youtube': 'rgba(255, 0, 0, 0.8)',
            'linkedin': 'rgba(0, 119, 181, 0.8)'
        };

        const ctx = document.getElementById('platformComparisonChart');
        if (!ctx) return;

        if (chartsMap.platform) {
            chartsMap.platform.destroy();
        }

        chartsMap.platform = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.map(d => d.content_type.toUpperCase()),
                datasets: [{
                    data: data.map(d => d.count),
                    backgroundColor: data.map(d => colors[d.content_type] || 'rgba(156, 163, 175, 0.8)'),
                    borderWidth: 2,
                    borderColor: '#1e293b'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#94a3b8',
                            padding: 15,
                            font: { size: 11 }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(11, 90, 142, 0.95)',
                        titleColor: '#f9fafb',
                        bodyColor: '#d1d5db',
                        borderColor: '#374151',
                        borderWidth: 1,
                        padding: 12
                    }
                }
            }
        });
    } catch (error) {
        console.error('Failed to load platform comparison chart:', error);
    }
}

// Content Type Distribution Chart
async function loadContentTypeChart() {
    try {
        const response = await fetch(`${API_BASE}/reports/blocking-stats`);
        const data = await response.json();

        // Default empty state
        if (!data) {
            data = { healthy: 1, blocked: 0, running: 0, failed: 0 };
        }

        const ctx = document.getElementById('contentTypeChart');
        if (!ctx) return;

        if (chartsMap.contentType) {
            chartsMap.contentType.destroy();
        }

        chartsMap.contentType = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: ['Healthy', 'Blocked', 'Running', 'Failed'],
                datasets: [{
                    data: [data.healthy, data.blocked, data.running, data.failed],
                    backgroundColor: [
                        'rgba(16, 185, 129, 0.8)', // Success
                        'rgba(239, 68, 68, 0.8)',  // Error
                        'rgba(59, 130, 246, 0.8)', // Secondary
                        'rgba(245, 158, 11, 0.8)'  // Warning
                    ],
                    borderWidth: 2,
                    borderColor: '#1e293b'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#94a3b8',
                            font: { size: 12 }
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Failed to load content type chart:', error);
    }
}

// System Performance Radar Chart
async function loadRadarChart() {
    try {
        const ctx = document.getElementById('radarChart');
        if (!ctx) return;

        if (chartsMap.radar) {
            chartsMap.radar.destroy();
        }

        // Fetch multiple stats points to build the radar
        const sourcesResp = await fetch(`${API_BASE}/sources/`);
        const sources = await sourcesResp.json();

        const statsResp = await fetch(`${API_BASE}/crawler/stats`);
        const stats = await statsResp.json();

        // Calculate synthetic scores (normalized 0-100)
        const sourceCount = sources.length || 1;
        const totalDocs = stats.total_documents || 0;

        // Metrics calculation
        const velocityScore = Math.min((totalDocs / 100) * 10, 100); // Mock velocity
        const stabilityScore = 100 - (sources.filter(s => s.status === 'failed').length / sourceCount * 100);
        const diversityScore = new Set(sources.map(s => s.content_type)).size * 20; // 5 types = 100
        const volumeScore = Math.min(totalDocs / 10, 100);
        const efficiencyScore = 85; // Placeholder

        chartsMap.radar = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ['Crawl Velocity', 'System Stability', 'Source Diversity', 'Data Volume', 'Efficiency'],
                datasets: [{
                    label: 'Current Performance',
                    data: [velocityScore, stabilityScore, diversityScore, volumeScore, efficiencyScore],
                    backgroundColor: 'rgba(6, 182, 212, 0.2)', // Accent
                    borderColor: 'rgba(6, 182, 212, 1)',
                    pointBackgroundColor: 'rgba(6, 182, 212, 1)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgba(6, 182, 212, 1)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        angleLines: { color: 'rgba(148, 163, 184, 0.1)' },
                        grid: { color: 'rgba(148, 163, 184, 0.1)' },
                        pointLabels: {
                            color: '#94a3b8',
                            font: { size: 12 }
                        },
                        ticks: {
                            backdropColor: 'transparent',
                            color: 'transparent' // Hide numbers for cleaner look
                        },
                        suggestedMin: 0,
                        suggestedMax: 100
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });

    } catch (error) {
        console.error('Failed to load radar chart:', error);
    }
}

// Export function for compatibility
window.loadCharts = loadCharts;
