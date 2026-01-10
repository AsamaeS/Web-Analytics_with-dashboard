// Project Management Logic

let currentProjectId = null;
let projects = [];

// Load projects on page load
async function loadProjects() {
    try {
        const response = await fetch(`${API_BASE}/projects`);
        if (!response.ok) throw new Error('Network response was not ok');
        projects = await response.json();
    } catch (error) {
        console.error('Failed to load projects:', error);
        projects = []; // Ensure empty array on error
    } finally {
        renderProjectSelector(); // Always render, so empty state (with Create button) shows up
    }

    // Auto-select first project if exists
    if (projects.length > 0 && !currentProjectId) {
        currentProjectId = projects[0].id;
        onProjectChange();
    }
}

function renderProjectSelector() {
    const container = document.getElementById('project-selector-container');
    if (!container) return;

    if (projects.length === 0) {
        container.innerHTML = `
            <div class="project-empty-state">
                <p class="text-muted">No projects yet</p>
                <button class="btn btn-primary btn-sm" onclick="openProjectModal()">Create Project</button>
            </div>
        `;
        return;
    }

    const currentProject = projects.find(p => p.id === currentProjectId) || projects[0];

    container.innerHTML = `
        <div style="display: flex; gap: 8px; align-items: center; width: 100%;">
            <div class="project-selector" style="flex: 1; min-width: 0;" onclick="toggleProjectDropdown()">
                <div class="project-icon">${currentProject.icon}</div>
                <div class="project-info">
                    <div class="project-name">${escapeHtml(currentProject.name)}</div>
                    <div class="project-domain">${escapeHtml(currentProject.domain)}</div>
                </div>
                <button class="btn-icon">▼</button>
            </div>
            <button class="btn btn-primary" onclick="openProjectModal()" title="Create New Project" style="height: 100%; aspect-ratio: 1; padding: 0; display: flex; align-items: center; justify-content: center; font-size: 1.25rem;">
                +
            </button>
        </div>
        
        <div class="project-dropdown" id="project-dropdown" style="display: none;">
            ${projects.map(p => `
                <div class="project-dropdown-item ${p.id === currentProjectId ? 'active' : ''}" 
                     onclick="selectProject('${p.id}')">
                    <span class="project-icon-sm">${p.icon}</span>
                    <div>
                        <div class="project-name-sm">${escapeHtml(p.name)}</div>
                        <div class="project-domain-sm">${escapeHtml(p.domain)}</div>
                    </div>
                </div>
            `).join('')}
            <hr style="margin: 0.5rem 0;">
            <div class="project-dropdown-item" onclick="openProjectModal()">
                <span class="project-icon-sm">➕</span>
                <div class="project-name-sm">New Project</div>
            </div>
        </div>
    `;

    renderRecentProjects();
}

function renderRecentProjects() {
    const listContainer = document.getElementById('recent-projects-nav');
    if (!listContainer) return;

    if (projects.length === 0) {
        listContainer.innerHTML = '<div class="text-muted" style="padding: 0.5rem 1rem; font-size: 0.75rem;">No projects yet</div>';
        return;
    }

    listContainer.innerHTML = projects.map(p => `
        <div class="nav-item ${p.id === currentProjectId ? 'active' : ''}" 
             style="cursor: pointer; padding: 0.5rem 1rem; font-size: 0.85rem; border-radius: 0; display: flex; align-items: center; gap: 8px; ${p.id === currentProjectId ? 'border-left: 3px solid var(--accent); background: rgba(255,255,255,0.05);' : ''}"
             onclick="selectProject('${p.id}')">
            <span style="font-size: 1rem;">${p.icon}</span> 
            <span style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${escapeHtml(p.name)}</span>
        </div>
    `).join('');
}

function toggleProjectDropdown() {
    const dropdown = document.getElementById('project-dropdown');
    dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
}

function selectProject(projectId) {
    currentProjectId = projectId;
    toggleProjectDropdown();
    renderProjectSelector();
    onProjectChange();
}

function onProjectChange() {
    // Update current project keywords display
    const project = projects.find(p => p.id === currentProjectId);
    if (project) {
        const keywordsContainer = document.getElementById('current-project-keywords');
        if (keywordsContainer) {
            keywordsContainer.innerHTML = project.keywords.length > 0
                ? project.keywords.map(k => `<span class="keyword-chip">${escapeHtml(k)}</span>`).join('')
                : '<span class="text-muted">No keywords defined</span>';
        }
    }

    // Reload data filtered by project
    if (currentTab === 'sources') {
        loadSources();
    } else if (currentTab === 'analytics') {
        loadCharts();
    } else if (currentTab === 'decision') {
        refreshDecisionSummary();
    }
}

function openProjectModal() {
    const modal = document.getElementById('project-modal');
    if (!modal) {
        createProjectModal();
    }

    // Reset form
    document.getElementById('project-form').reset();
    document.getElementById('project-modal-title').textContent = 'Create New Project';
    document.getElementById('project-id-field').value = '';

    // Show modal
    document.getElementById('project-modal-overlay').classList.add('active');
    toggleProjectDropdown(); // Close dropdown if open
}

function createProjectModal() {
    const modalHTML = `
        <div class="modal-overlay" id="project-modal-overlay">
            <div class="modal">
                <div class="modal-header">
                    <h2 class="modal-title" id="project-modal-title">Create New Project</h2>
                </div>
                <div class="modal-body">
                    <form id="project-form">
                        <input type="hidden" id="project-id-field">
                        
                        <div class="form-group">
                            <label class="form-label">Project Name *</label>
                            <input type="text" class="form-input" id="project-name" 
                                   placeholder="e.g., Healthcare Investment Analysis" required>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Domain *</label>
                            <select class="form-input" id="project-domain" required>
                                <option value="">Select domain...</option>
                                <option value="Healthcare">Healthcare</option>
                                <option value="Finance">Finance</option>
                                <option value="Energy">Energy</option>
                                <option value="Technology">Technology</option>
                                <option value="Manufacturing">Manufacturing</option>
                                <option value="Retail">Retail</option>
                                <option value="Other">Other</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Keywords (comma-separated)</label>
                            <textarea class="form-input" id="project-keywords" rows="3"
                                      placeholder="e.g., hospital, medical, regulation, investment"></textarea>
                            <small class="text-muted">These keywords will guide data collection</small>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Icon</label>
                            <div class="icon-selector">
                                <button type="button" class="icon-btn" onclick="selectIcon('🏥')">🏥</button>
                                <button type="button" class="icon-btn" onclick="selectIcon('💰')">💰</button>
                                <button type="button" class="icon-btn" onclick="selectIcon('⚡')">⚡</button>
                                <button type="button" class="icon-btn" onclick="selectIcon('💻')">💻</button>
                                <button type="button" class="icon-btn" onclick="selectIcon('🏭')">🏭</button>
                                <button type="button" class="icon-btn" onclick="selectIcon('🛒')">🛒</button>
                                <button type="button" class="icon-btn" onclick="selectIcon('📊')">📊</button>
                            </div>
                            <input type="hidden" id="project-icon" value="📊">
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Description (optional)</label>
                            <textarea class="form-input" id="project-description" rows="2"
                                      placeholder="Brief description of the project objective"></textarea>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="closeProjectModal()">Cancel</button>
                    <button class="btn btn-primary" onclick="saveProject()">Create Project</button>
                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHTML);
}

function selectIcon(icon) {
    document.getElementById('project-icon').value = icon;
    document.querySelectorAll('.icon-btn').forEach(btn => btn.classList.remove('selected'));
    event.target.classList.add('selected');
}

function closeProjectModal() {
    document.getElementById('project-modal-overlay').classList.remove('active');
}

async function saveProject() {
    const projectId = document.getElementById('project-id-field').value;
    const name = document.getElementById('project-name').value.trim();
    const domain = document.getElementById('project-domain').value;
    const keywordsText = document.getElementById('project-keywords').value.trim();
    const icon = document.getElementById('project-icon').value;
    const description = document.getElementById('project-description').value.trim();

    if (!name || !domain) {
        alert('Please fill in required fields');
        return;
    }

    const keywords = keywordsText ? keywordsText.split(',').map(k => k.trim()).filter(k => k) : [];

    const projectData = {
        name,
        domain,
        keywords,
        icon,
        description: description || undefined
    };

    try {
        const url = projectId ? `${API_BASE}/projects/${projectId}` : `${API_BASE}/projects/`;
        const method = projectId ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(projectData)
        });

        if (!response.ok) throw new Error('Failed to save project');

        closeProjectModal();
        await loadProjects();

        // Select the new project if it was just created
        if (!projectId) {
            const result = await response.json();
            if (result.id) {
                currentProjectId = result.id;
                onProjectChange();
            }
        }
    } catch (error) {
        console.error('Failed to save project:', error);
        alert('Failed to save project. Please try again.');
    }
}

// Expose functions globally
window.loadProjects = loadProjects;
window.selectProject = selectProject;
window.toggleProjectDropdown = toggleProjectDropdown;
window.openProjectModal = openProjectModal;
window.closeProjectModal = closeProjectModal;
window.saveProject = saveProject;
window.selectIcon = selectIcon;
