// Configuration
const CONFIG = {
    // These will be auto-detected from the page URL
    owner: 'tristan-mcinnis', // GitHub username
    repo: 'xhs-market-research', // Repository name
    workflowFileName: 'web-scrape.yml',
    pollInterval: 5000, // 5 seconds
    maxPollAttempts: 120, // 10 minutes max (5s * 120)
    // Password hash (SHA-256 of your password)
    // Generate with: echo -n "your_password" | shasum -a 256
    // Or use: https://emn178.github.io/online-tools/sha256.html
    passwordHash: '6fd4add0da2d3092c5c8c9b7831762d68ce767070d48ae33934c6a41f9f1c7bb', // Default: "password"
    // GitHub PAT - WARNING: Visible in page source! Password provides basic protection.
    githubToken: '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',
};

// State
let currentWorkflowRunId = null;
let pollAttempts = 0;
let pollInterval = null;

// Password Gate
document.getElementById('password-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const password = document.getElementById('password-input').value;
    const errorEl = document.getElementById('password-error');

    // Hash the input password
    const hash = await sha256(password);

    if (hash === CONFIG.passwordHash) {
        // Success - show main interface
        document.getElementById('password-gate').classList.add('hidden');
        document.getElementById('main-interface').classList.remove('hidden');
        sessionStorage.setItem('authenticated', 'true');
        initializeInterface();
    } else {
        errorEl.textContent = 'Incorrect password';
        document.getElementById('password-input').value = '';
    }
});

// Logout
document.getElementById('logout-btn').addEventListener('click', () => {
    sessionStorage.removeItem('authenticated');
    document.getElementById('password-gate').classList.remove('hidden');
    document.getElementById('main-interface').classList.add('hidden');
    document.getElementById('password-input').value = '';
    document.getElementById('password-error').textContent = '';
});

// Check if already authenticated
window.addEventListener('load', () => {
    if (sessionStorage.getItem('authenticated') === 'true') {
        document.getElementById('password-gate').classList.add('hidden');
        document.getElementById('main-interface').classList.remove('hidden');
        initializeInterface();
    }
});

// Audit log refresh
document.getElementById('refresh-audit-btn').addEventListener('click', loadAuditLog);

// Initialize interface
function initializeInterface() {
    // Auto-detect repo from GitHub Pages URL
    if (window.location.hostname.includes('github.io')) {
        const pathParts = window.location.pathname.split('/').filter(p => p);
        if (pathParts.length > 0) {
            CONFIG.owner = window.location.hostname.split('.')[0];
            CONFIG.repo = pathParts[0] || CONFIG.repo;
        }
    }

    document.getElementById('repo-name').textContent = `${CONFIG.owner}/${CONFIG.repo}`;

    // Load audit log
    loadAuditLog();
}

// Form submission
document.getElementById('scraper-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const keywords = document.getElementById('keywords').value.trim().split(/\s+/);
    const maxItems = parseInt(document.getElementById('max-items').value);
    const maxDownloads = document.getElementById('max-downloads').value
        ? parseInt(document.getElementById('max-downloads').value)
        : 0;
    const downloadImages = document.getElementById('download-images').checked;

    // Show status card
    document.getElementById('status-card').classList.remove('hidden');
    document.getElementById('results-card').classList.add('hidden');
    document.getElementById('run-btn').disabled = true;

    try {
        const runId = await triggerWorkflow({
            keywords: keywords.join(' '),
            maxItems,
            maxDownloads,
            downloadImages
        });

        currentWorkflowRunId = runId;
        updateStatus('Workflow triggered', 'Running...');

        // Start polling
        pollAttempts = 0;
        startPolling(runId);
    } catch (error) {
        showError('Failed to trigger workflow: ' + error.message);
        document.getElementById('run-btn').disabled = false;
    }
});

// Trigger GitHub Actions workflow
async function triggerWorkflow(inputs) {
    const token = document.getElementById('github-token').value || CONFIG.githubToken;
    const url = `https://api.github.com/repos/${CONFIG.owner}/${CONFIG.repo}/actions/workflows/${CONFIG.workflowFileName}/dispatches`;

    const headers = {
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json',
    };

    if (token && token !== 'REPLACE_WITH_YOUR_TOKEN') {
        headers['Authorization'] = `token ${token}`;
    }

    const response = await fetch(url, {
        method: 'POST',
        headers,
        body: JSON.stringify({
            ref: 'main', // or 'master' depending on your default branch
            inputs: {
                keywords: inputs.keywords,
                max_items: inputs.maxItems.toString(),
                max_downloads: inputs.maxDownloads.toString(),
                download_images: inputs.downloadImages.toString(),
            }
        })
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || `HTTP ${response.status}`);
    }

    // GitHub API doesn't return the run ID in the dispatch response
    // We need to poll the runs endpoint to find the latest run
    await sleep(2000); // Wait 2 seconds for the run to appear
    return await getLatestWorkflowRun();
}

// Get latest workflow run
async function getLatestWorkflowRun() {
    const token = document.getElementById('github-token').value || CONFIG.githubToken;
    const url = `https://api.github.com/repos/${CONFIG.owner}/${CONFIG.repo}/actions/workflows/${CONFIG.workflowFileName}/runs?per_page=1`;

    const headers = {
        'Accept': 'application/vnd.github.v3+json',
    };

    if (token && token !== 'REPLACE_WITH_YOUR_TOKEN') {
        headers['Authorization'] = `token ${token}`;
    }

    const response = await fetch(url, { headers });

    if (!response.ok) {
        throw new Error(`Failed to fetch workflow runs: HTTP ${response.status}`);
    }

    const data = await response.json();

    if (data.workflow_runs && data.workflow_runs.length > 0) {
        return data.workflow_runs[0].id;
    }

    throw new Error('No workflow runs found');
}

// Poll workflow status
function startPolling(runId) {
    if (pollInterval) {
        clearInterval(pollInterval);
    }

    pollInterval = setInterval(async () => {
        try {
            const status = await checkWorkflowStatus(runId);
            updateProgress((pollAttempts / CONFIG.maxPollAttempts) * 100);

            if (status.conclusion) {
                // Workflow completed
                clearInterval(pollInterval);
                handleWorkflowCompletion(status);
            } else {
                // Still running
                updateStatus('Running', status.status);
                pollAttempts++;

                if (pollAttempts >= CONFIG.maxPollAttempts) {
                    clearInterval(pollInterval);
                    showError('Workflow timeout - check GitHub Actions page for details');
                }
            }
        } catch (error) {
            clearInterval(pollInterval);
            showError('Polling error: ' + error.message);
        }
    }, CONFIG.pollInterval);
}

// Check workflow status
async function checkWorkflowStatus(runId) {
    const token = document.getElementById('github-token').value || CONFIG.githubToken;
    const url = `https://api.github.com/repos/${CONFIG.owner}/${CONFIG.repo}/actions/runs/${runId}`;

    const headers = {
        'Accept': 'application/vnd.github.v3+json',
    };

    if (token && token !== 'REPLACE_WITH_YOUR_TOKEN') {
        headers['Authorization'] = `token ${token}`;
    }

    const response = await fetch(url, { headers });

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }

    return await response.json();
}

// Handle workflow completion
async function handleWorkflowCompletion(status) {
    updateProgress(100);

    document.getElementById('status-card').classList.add('hidden');
    document.getElementById('results-card').classList.remove('hidden');
    document.getElementById('run-btn').disabled = false;

    document.getElementById('workflow-id').textContent = status.id;
    document.getElementById('final-status').textContent = status.conclusion;
    document.getElementById('completion-time').textContent = new Date(status.updated_at).toLocaleString();

    if (status.conclusion === 'success') {
        // Show download button
        document.getElementById('download-section').classList.remove('hidden');
        document.getElementById('error-section').classList.add('hidden');

        // Fetch artifacts
        const artifacts = await getWorkflowArtifacts(status.id);
        if (artifacts && artifacts.length > 0) {
            setupDownloadButton(artifacts[0]);
        }
    } else {
        // Show error
        document.getElementById('download-section').classList.add('hidden');
        document.getElementById('error-section').classList.remove('hidden');
        document.getElementById('error-message').textContent = `Workflow ${status.conclusion}`;
    }
}

// Get workflow artifacts
async function getWorkflowArtifacts(runId) {
    const token = document.getElementById('github-token').value || CONFIG.githubToken;
    const url = `https://api.github.com/repos/${CONFIG.owner}/${CONFIG.repo}/actions/runs/${runId}/artifacts`;

    const headers = {
        'Accept': 'application/vnd.github.v3+json',
    };

    if (token && token !== 'REPLACE_WITH_YOUR_TOKEN') {
        headers['Authorization'] = `token ${token}`;
    }

    const response = await fetch(url, { headers });

    if (!response.ok) {
        throw new Error(`Failed to fetch artifacts: HTTP ${response.status}`);
    }

    const data = await response.json();
    return data.artifacts || [];
}

// Setup download button
function setupDownloadButton(artifact) {
    const downloadBtn = document.getElementById('download-btn');
    downloadBtn.onclick = () => {
        // GitHub requires authentication to download artifacts
        // Redirect to the artifact download URL
        const downloadUrl = `https://github.com/${CONFIG.owner}/${CONFIG.repo}/actions/runs/${currentWorkflowRunId}/artifacts/${artifact.id}`;
        window.open(downloadUrl, '_blank');
    };
}

// View logs button
document.getElementById('view-logs-btn').addEventListener('click', () => {
    const logsUrl = `https://github.com/${CONFIG.owner}/${CONFIG.repo}/actions/runs/${currentWorkflowRunId}`;
    window.open(logsUrl, '_blank');
});

// UI helpers
function updateStatus(workflow, progress) {
    document.getElementById('workflow-status').textContent = workflow;
    document.getElementById('workflow-progress').textContent = progress;
}

function updateProgress(percent) {
    document.getElementById('progress-fill').style.width = `${percent}%`;
}

function showError(message) {
    document.getElementById('status-card').classList.add('hidden');
    document.getElementById('results-card').classList.remove('hidden');
    document.getElementById('download-section').classList.add('hidden');
    document.getElementById('error-section').classList.remove('hidden');
    document.getElementById('error-message').textContent = message;
    document.getElementById('run-btn').disabled = false;
}

// Utility: SHA-256 hash
async function sha256(message) {
    const msgBuffer = new TextEncoder().encode(message);
    const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

// Utility: Sleep
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Audit Log Functions
async function loadAuditLog() {
    const container = document.getElementById('audit-log-container');
    container.innerHTML = '<p class="loading">Loading audit log...</p>';

    try {
        const response = await fetch('audit.json');
        if (!response.ok) {
            throw new Error('Failed to load audit log');
        }

        const auditEntries = await response.json();
        displayAuditLog(auditEntries);
    } catch (error) {
        container.innerHTML = '<p class="error">Failed to load audit log. It may not exist yet.</p>';
    }
}

function displayAuditLog(entries) {
    const container = document.getElementById('audit-log-container');

    if (!entries || entries.length === 0) {
        container.innerHTML = '<p class="empty-state">No scrapes recorded yet. Run your first scrape to populate the audit log.</p>';
        updateAuditStats(0, 0, 0);
        return;
    }

    // Calculate stats
    const totalRuns = entries.length;
    const totalPosts = entries.reduce((sum, e) => sum + (e.posts_scraped || 0), 0);
    const totalImages = entries.reduce((sum, e) => sum + (e.images_downloaded || 0), 0);
    updateAuditStats(totalRuns, totalPosts, totalImages);

    // Create table
    const table = document.createElement('table');
    table.className = 'audit-table';

    // Header
    const thead = document.createElement('thead');
    thead.innerHTML = `
        <tr>
            <th>Date</th>
            <th>Keywords</th>
            <th>Max Items</th>
            <th>Posts</th>
            <th>Images</th>
            <th>Status</th>
            <th>Link</th>
        </tr>
    `;
    table.appendChild(thead);

    // Body
    const tbody = document.createElement('tbody');
    entries.forEach(entry => {
        const row = document.createElement('tr');
        row.className = entry.status === 'success' ? 'success-row' : 'failed-row';

        const date = new Date(entry.timestamp);
        const dateStr = date.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });

        row.innerHTML = `
            <td>${dateStr}</td>
            <td><strong>${escapeHtml(entry.keywords)}</strong></td>
            <td>${entry.max_items}</td>
            <td>${entry.posts_scraped || 0}</td>
            <td>${entry.download_images === 'true' || entry.download_images === true ? entry.images_downloaded || 0 : 'N/A'}</td>
            <td><span class="status-badge status-${entry.status}">${entry.status}</span></td>
            <td><a href="${entry.run_url}" target="_blank" class="run-link">View</a></td>
        `;
        tbody.appendChild(row);
    });
    table.appendChild(tbody);

    container.innerHTML = '';
    container.appendChild(table);
}

function updateAuditStats(runs, posts, images) {
    document.getElementById('total-runs').textContent = runs;
    document.getElementById('total-posts').textContent = posts;
    document.getElementById('total-images').textContent = images;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
