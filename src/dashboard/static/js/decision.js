// Decision Intelligence Logic - MVP PROTOTYPE

async function refreshDecisionSummary() {
    const tldr = document.getElementById('decision-tldr-content');
    const insightsList = document.getElementById('strategic-insights-list');
    
    tldr.innerHTML = '<span class="text-muted">Analyzing NoSQL truth...</span>';
    
    try {
        const response = await fetch(`${API_BASE}/decision/summary`);
        const data = await response.json();
        
        // Render TL;DR
        tldr.innerHTML = data.tldr;
        
        // Render Insights
        insightsList.innerHTML = data.insights.map(info => `
            <div class="insight-item">
                <div class="insight-type">${info.type} / ${Math.round(info.confidence * 100)}% Confidence</div>
                <div class="insight-text">${info.text}</div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Decision summary failed:', error);
        tldr.innerHTML = '<span class="text-destructive">Failed to generate intelligence briefing.</span>';
    }
}

async function loadSignalRadar() {
    const ctx = document.getElementById('signalRadarChart');
    if (!ctx) return;
    
    // Logic to simulate signal radar using crawl volume
    // In a real scenario, this would be an actual API call
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00'],
            datasets: [{
                label: 'Signal Intensity',
                data: [12, 19, 3, 5, 32, 23, 10], // Anomalous spike at 14:00
                borderColor: '#0078d4',
                backgroundColor: 'rgba(0, 120, 212, 0.1)',
                pointBackgroundColor: (context) => context.raw > 25 ? '#ef4444' : '#0078d4',
                pointRadius: (context) => context.raw > 25 ? 8 : 4,
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            plugins: { legend: { display: false } },
            scales: {
                y: { grid: { color: '#374151' }, ticks: { color: '#9ca3af' } },
                x: { grid: { display: false }, ticks: { color: '#9ca3af' } }
            }
        }
    });
}

function loadConceptClusters() {
    const ctx = document.getElementById('conceptClusterChart');
    if (!ctx) return;
    
    new Chart(ctx, {
        type: 'bubble',
        data: {
            datasets: [
                { label: 'Healthcare', data: [{x: 20, y: 30, r: 15}], backgroundColor: 'rgba(59, 130, 246, 0.5)' },
                { label: 'Finance', data: [{x: 40, y: 10, r: 25}], backgroundColor: 'rgba(16, 185, 129, 0.5)' },
                { label: 'Energy', data: [{x: 30, y: 20, r: 10}], backgroundColor: 'rgba(245, 158, 11, 0.5)' },
                { label: 'Regulatory', data: [{x: 45, y: 40, r: 20}], backgroundColor: 'rgba(139, 92, 246, 0.5)' }
            ]
        },
        options: {
            plugins: { legend: { position: 'bottom' } },
            scales: {
                y: { display: false },
                x: { display: false }
            }
        }
    });
}

async function sendSidecarQuery() {
    const input = document.getElementById('sidecar-query-input');
    const history = document.getElementById('sidecar-chat-history');
    const msg = input.value;
    
    if (!msg) return;
    
    // Add user msg
    const userDiv = document.createElement('div');
    userDiv.className = 'chat-msg user';
    userDiv.textContent = msg;
    history.appendChild(userDiv);
    input.value = '';
    
    // Add assistant thinking
    const assistantDiv = document.createElement('div');
    assistantDiv.className = 'chat-msg assistant';
    assistantDiv.textContent = 'Analyzing NoSQL grounding...';
    history.appendChild(assistantDiv);
    history.scrollTop = history.scrollHeight;
    
    try {
        const response = await fetch(`${API_BASE}/decision/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: msg })
        });
        const data = await response.json();
        assistantDiv.textContent = data.text;
    } catch (error) {
        assistantDiv.textContent = 'Error connecting to Decision Assistant core.';
    }
}

// Global exposure
window.refreshDecisionSummary = refreshDecisionSummary;
window.sendSidecarQuery = sendSidecarQuery;
