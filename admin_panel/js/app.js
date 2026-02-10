const api = new APIClient();
let currentUserId = null;
let commandPollInterval = null;
let currentBrowserData = null; // Added for browser drill-down

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    loadDashboard();

    // Auto-refresh stats/users every 10s
    setInterval(() => {
        if (document.visibilityState === 'visible') loadDashboard();
    }, 10000);

    document.getElementById('logoutBtn').addEventListener('click', () => api.logout());
    document.getElementById('refreshUsersBtn').addEventListener('click', loadDashboard);

    initCharts();
});

function initCharts() {
    // Pie Chart: Applications Usage
    const ctxPie = document.getElementById('appsChart').getContext('2d');
    new Chart(ctxPie, {
        type: 'doughnut',
        data: {
            labels: ['Chrome', 'Word', 'Slack', 'Others'],
            datasets: [{
                data: [45, 25, 20, 10],
                backgroundColor: [
                    '#ef4444', // Red (Chrome)
                    '#8b5cf6', // Purple (Word)
                    '#3b82f6', // Blue (Slack)
                    '#1f2937'  // Dark (Others)
                ],
                borderWidth: 0,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: { boxWidth: 10, font: { size: 10 } }
                }
            },
            cutout: '70%'
        }
    });

    // Bar Chart: Weekly Active Hours
    const ctxBar = document.getElementById('hoursChart').getContext('2d');
    new Chart(ctxBar, {
        type: 'bar',
        data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
            datasets: [{
                label: 'Hours',
                data: [6, 8, 7, 5, 8],
                backgroundColor: '#3b82f6',
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true, grid: { display: false }, ticks: { display: false } },
                x: { grid: { display: false }, ticks: { font: { size: 10 } } }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

async function checkAuth() {
    const token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = 'login.html';
        return;
    }
    // Optional: Verify token validity with backend here if needed
}

async function loadDashboard() {
    try {
        const [onlineData, allUsers] = await Promise.all([
            api.getOnlineUsers(),
            api.getAllUsers()
        ]);

        updateStats(onlineData.users.length, allUsers.length);
        renderUserList(allUsers, onlineData.users);
    } catch (err) {
        console.error("Dashboard refresh failed", err);
    }
}

function updateStats(onlineCount, totalCount) {
    const offlineCount = Math.max(0, totalCount - onlineCount);

    // Sidebar Stats
    const totalEl = document.getElementById('totalUserCount');
    if (totalEl) totalEl.textContent = totalCount;

    const onlineEl = document.getElementById('sidebarOnlineCount');
    if (onlineEl) onlineEl.textContent = onlineCount;

    const offlineEl = document.getElementById('sidebarOfflineCount');
    if (offlineEl) offlineEl.textContent = offlineCount;

    // Detail View Stats (if user selected)
    // Here we might fetch specific details later
}

function renderUserList(allUsers, onlineUsers) {
    const listContainer = document.getElementById('usersList');
    const onlineIds = new Set(onlineUsers.map(u => u.user_id));

    listContainer.innerHTML = '';

    allUsers.forEach(user => {
        const isOnline = onlineIds.has(user.id);
        const el = document.createElement('div');
        // Match Sidebar styling
        el.className = `px-4 py-3 cursor-pointer text-sm flex items-center justify-between group transition-colors duration-200 ${currentUserId === user.id ? 'bg-slate-800 border-l-4 border-blue-500' : 'hover:bg-slate-800 border-l-4 border-transparent'}`;
        el.onclick = () => selectUser(user, isOnline);

        el.innerHTML = `
            <div class="flex items-center w-full">
                <div class="relative mr-3">
                    <div class="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-xs font-bold text-slate-300 border border-slate-600">
                        ${user.name.charAt(0).toUpperCase()}
                    </div>
                    <div class="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-2 border-slate-900 ${isOnline ? 'bg-green-500' : 'bg-slate-500'}"></div>
                </div>
                <div class="min-w-0 flex-1">
                    <h4 class="font-medium text-slate-200 truncate group-hover:text-white transition">${user.name}</h4>
                    <p class="text-xs text-slate-500 truncate">${user.email}</p>
                </div>
                <i class="fas fa-chevron-right text-xs text-slate-600 group-hover:text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity"></i>
            </div>
        `;
        listContainer.appendChild(el);
    });
}

function selectUser(user, isOnline) {
    currentUserId = user.id;

    // UI Updates
    document.getElementById('noUserSelected').classList.add('hidden');
    document.getElementById('userDashboard').classList.remove('hidden');

    // Header Name
    const headerName = document.getElementById('selectedUserNameHeader');
    if (headerName) {
        headerName.textContent = user.name;
        headerName.classList.remove('hidden');
    }

    // Detail Stats
    const statusEl = document.getElementById('detailStatus');
    if (statusEl) {
        statusEl.textContent = isOnline ? 'Online' : 'Offline';
        statusEl.className = isOnline
            ? 'text-2xl font-extrabold text-green-600 mt-0.5'
            : 'text-2xl font-extrabold text-gray-800 mt-0.5';
    }

    // Reset Live Feed
    updateLiveFeed('reset');

    // Refresh List to show active state
    loadDashboard();

    // Clear logs
    clearLogs();
    log(`Selected user: ${user.name}`);
    loadHistory(user.id);
}

// ------ Live Feed Management ------

function updateLiveFeed(type, data) {
    const container = document.getElementById('liveFeedContainer');
    const placeholder = document.getElementById('feedPlaceholder');
    const image = document.getElementById('feedImage');
    const list = document.getElementById('feedList');
    const loading = document.getElementById('feedLoading');
    const titleEl = document.getElementById('liveFeedTitle');

    // Hide all first
    placeholder.classList.add('hidden');
    image.classList.add('hidden');
    list.classList.add('hidden');
    loading.classList.add('hidden');

    if (type === 'reset') {
        placeholder.classList.remove('hidden');
        if (titleEl) titleEl.textContent = 'Live Feed';
        return;
    }

    if (type === 'loading') {
        loading.classList.remove('hidden');
        // Keep previous content visible behind loading overlay? Or just show overlay?
        // Let's keep placeholder visible if nothing else
        if (image.src === "" && list.innerHTML === "") placeholder.classList.remove('hidden');
        return;
    }

    if (type === 'image') {
        image.src = data;
        image.classList.remove('hidden');
        if (titleEl) titleEl.textContent = 'Remote Screen Capture';
    } else if (type === 'apps') {
        list.innerHTML = `
            <div class="mb-4 text-xs font-bold text-gray-500 uppercase tracking-widest border-b border-gray-800 pb-2">Active Processes</div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
                ${data.map(app => `
                    <div class="flex items-center space-x-2 p-2 bg-gray-900/50 rounded border border-gray-800">
                        <i class="fas fa-microchip text-blue-500 text-[10px]"></i>
                        <span class="text-xs text-gray-300 truncate">${app.name || app}</span>
                        <span class="text-[10px] text-gray-600 ml-auto">PID: ${app.pid || 'N/A'}</span>
                    </div>
                `).join('')}
            </div>
        `;
        list.classList.remove('hidden');
        if (titleEl) titleEl.textContent = 'Running Applications';
    } else if (type === 'browser') {
        console.log("DEBUG: Received Browser Data:", data);

        let details = data.details;
        if (typeof details === 'string') {
            try { details = JSON.parse(details); } catch (e) { console.error("Parse error:", e); }
        }

        // Store for interactive navigation
        currentBrowserData = details;

        renderBrowserList();

        list.classList.remove('hidden');
        if (titleEl) titleEl.textContent = 'Browser Activity Monitoring';
    }
}

/**
 * Interactive Drill-down: List of Browsers
 */
function renderBrowserList() {
    if (!currentBrowserData) return;
    const list = document.getElementById('feedList');
    const sessions = currentBrowserData.sessions || {};

    let html = `
        <div class="mb-4 text-xs font-bold text-gray-500 uppercase tracking-widest border-b border-gray-800 pb-2">Detected Browsers</div>
        <div class="grid grid-cols-1 gap-3">
    `;

    const browserNames = Object.keys(sessions);
    if (browserNames.length === 0) {
        html += `<div class="text-gray-600 italic p-10 text-center">No browsers with detailed tab information detected.</div>`;
    } else {
        browserNames.forEach(name => {
            const count = sessions[name].length;
            html += `
                <div onclick="renderTabList('${name}')" class="flex items-center justify-between p-4 bg-gray-900/50 rounded-xl border border-gray-800 hover:border-blue-500 hover:bg-blue-500/5 cursor-pointer transition-all group">
                    <div class="flex items-center">
                        <div class="w-10 h-10 rounded-full bg-blue-500/10 flex items-center justify-center mr-4 group-hover:scale-110 transition-transform">
                            <i class="fab fa-${name.toLowerCase()} text-blue-500 text-lg"></i>
                        </div>
                        <div>
                            <div class="text-sm font-bold text-gray-200 group-hover:text-blue-400 transition-colors uppercase tracking-tight">${name}</div>
                            <div class="text-[10px] text-gray-500 uppercase tracking-wider">${count} Open Tabs</div>
                        </div>
                    </div>
                    <i class="fas fa-chevron-right text-gray-700 group-hover:text-blue-500 transition-colors"></i>
                </div>
            `;
        });
    }

    html += `</div>`;
    list.innerHTML = html;
}

/**
 * Interactive Drill-down: List of Tabs for Browser
 */
function renderTabList(browserName) {
    if (!currentBrowserData || !currentBrowserData.sessions[browserName]) return;
    const list = document.getElementById('feedList');
    const tabs = currentBrowserData.sessions[browserName];

    let html = `
        <div class="flex items-center mb-4 pb-2 border-b border-gray-800">
            <button onclick="renderBrowserList()" class="w-8 h-8 rounded-full bg-gray-800 flex items-center justify-center mr-3 hover:bg-gray-700 transition">
                <i class="fas fa-arrow-left text-xs"></i>
            </button>
            <div class="text-xs font-bold text-gray-300 uppercase tracking-widest flex items-center">
                <i class="fab fa-${browserName.toLowerCase()} mr-2 text-blue-400"></i> ${browserName} TABS
            </div>
            <span class="ml-auto px-2 py-0.5 bg-gray-800 rounded text-[10px] text-gray-500">${tabs.length}</span>
        </div>
        <div class="space-y-3">
    `;

    tabs.forEach(tab => {
        const urlStr = tab.url ? `<div class="text-[10px] text-blue-400/60 truncate mt-1 italic hover:underline cursor-pointer">${tab.url}</div>` : '';
        html += `
            <div class="p-3 bg-gray-900/40 rounded-lg border border-gray-800/50 hover:border-blue-500/30 transition-all overflow-hidden group">
                <div class="flex items-start">
                    <div class="w-6 h-6 rounded bg-gray-800 flex items-center justify-center mr-3 shrink-0 group-hover:bg-blue-500/10 transition-colors">
                        <i class="fas fa-globe text-[10px] text-gray-600 group-hover:text-blue-500"></i>
                    </div>
                    <div class="min-w-0 flex-1">
                        <div class="text-xs text-gray-200 font-medium leading-normal">${tab.title}</div>
                        ${urlStr}
                    </div>
                </div>
            </div>
        `;
    });

    html += `</div>`;
    list.innerHTML = html;
}


async function triggerCommand(commandType) {
    if (!currentUserId) return;

    // Update Title for Immediate Feedback
    const titleEl = document.getElementById('liveFeedTitle');
    if (titleEl) {
        if (commandType === 'TAKE_SCREENSHOT') titleEl.textContent = 'Requesting Screenshot...';
        if (commandType === 'GET_RUNNING_APPS') titleEl.textContent = 'Fetching Running Apps...';
        if (commandType === 'GET_BROWSER_STATUS') titleEl.textContent = 'Checking Browser Activity...';
    }

    updateLiveFeed('loading');
    log(`Sending command: ${commandType}...`);

    try {
        const res = await api.sendCommand(currentUserId, commandType);
        log(`Command SENT. ID: ${res.command_id}`, 'success');
        pollForCommandResult(res.command_id, commandType, currentUserId);

    } catch (err) {
        log(`Failed to send command: ${err.message}`, 'error');
        updateLiveFeed('reset');
    }
}

async function pollForCommandResult(commandId, type, userId) {
    let attempts = 0;
    const maxAttempts = 15; // 30 seconds

    if (commandPollInterval) clearInterval(commandPollInterval);

    commandPollInterval = setInterval(async () => {
        attempts++;
        if (attempts > maxAttempts) {
            clearInterval(commandPollInterval);
            log(`Timeout waiting for ${type} result.`, 'warning');
            updateLiveFeed('reset');
            return;
        }

        try {
            if (type === 'TAKE_SCREENSHOT') {
                const res = await api.getScreenshot(commandId);
                if (res.url) {
                    clearInterval(commandPollInterval);
                    log(`Screenshot received!`, 'success');
                    updateLiveFeed('image', res.url);

                    // Also update stats card
                    const countEl = document.getElementById('detailScreenshots');
                    if (countEl) countEl.textContent = parseInt(countEl.textContent || 0) + 1;
                }
            } else if (type === 'GET_RUNNING_APPS') {
                const history = await api.getCommandHistory(userId);
                const cmd = history.find(c => c.id === commandId);
                if (cmd && cmd.status === 'EXECUTED') {
                    clearInterval(commandPollInterval);
                    const appsData = await api.getApps(userId);
                    log(`Apps received: ${appsData.apps.length} running.`, 'success');
                    updateLiveFeed('apps', appsData.apps);

                    // Update stats card
                    const appEl = document.getElementById('detailApp');
                    if (appEl && appsData.apps.length > 0) {
                        appEl.textContent = appsData.apps[0].name || appsData.apps[0];
                        appEl.title = appsData.apps[0].name || appsData.apps[0];
                    }
                } else if (cmd && cmd.status === 'FAILED') {
                    clearInterval(commandPollInterval);
                    log('Command FAILED on client.', 'error');
                    updateLiveFeed('reset');
                }
            } else if (type === 'GET_BROWSER_STATUS') {
                const history = await api.getCommandHistory(userId);
                const cmd = history.find(c => c.id === commandId);
                if (cmd && cmd.status === 'EXECUTED') {
                    clearInterval(commandPollInterval);
                    const browserData = await api.getBrowser(userId);
                    log(`Browser: ${browserData.browser}`, 'success');
                    updateLiveFeed('browser', browserData);
                }
            }
        } catch (e) {
            // Ignore errors while polling
            console.log("Polling error:", e);
        }

    }, 2000);
}

// ------ Modals & Helpers ------

function showNotifyModal() {
    if (!currentUserId) return;
    document.getElementById('notifyModal').classList.remove('hidden');
}

function closeNotifyModal() { // Renamed to match HTML call? Wait, HTML calls document.getElementById... hidden.
    // HTML uses: onclick="document.getElementById('notifyModal').classList.add('hidden')"
    // But let's keep this clean
    document.getElementById('notifyModal').classList.add('hidden');
}

async function sendNotification() {
    const title = document.getElementById('notifyTitle').value;
    const msg = document.getElementById('notifyMessage').value;

    if (!title || !msg) return;

    try {
        await api.sendNotification(currentUserId, title, msg);
        log(`Notification sent: "${title}"`, 'success');
        document.getElementById('notifyModal').classList.add('hidden');
    } catch (err) {
        log(`Failed to send notification: ${err.message}`, 'error');
    }
}

// Modal closing logic is partly in HTML onclicks, keeping consistent
function closeModal() {
    document.getElementById('screenshotModal').classList.add('hidden');
}

// Logs
function log(msg, type = 'info') {
    const logContainer = document.getElementById('commandLogTable'); // This is a table body in restored HTML?
    // Wait, HTML has <tbody id="commandLogTable">
    // Previous app.js was targeting outputLog div.
    // Restored HTML (Line 231): <tbody id="commandLogTable" class="divide-y divide-gray-50"></tbody>

    if (!logContainer) return;

    const row = document.createElement('tr');
    const time = new Date().toLocaleTimeString();

    let statusColor = 'text-gray-500';
    if (type === 'success') statusColor = 'text-green-500 font-bold';
    if (type === 'error') statusColor = 'text-red-500 font-bold';
    if (type === 'warning') statusColor = 'text-yellow-500';

    row.innerHTML = `
        <td class="p-2 text-gray-700 font-medium">${msg}</td>
        <td class="p-2 ${statusColor} text-xs uppercase">${type}</td>
        <td class="p-2 text-right text-gray-400 text-xs">${time}</td>
    `;

    logContainer.prepend(row);
}

function clearLogs() {
    const logContainer = document.getElementById('commandLogTable');
    if (logContainer) logContainer.innerHTML = '';
}

async function loadHistory(userId) {
    // Optional: Load persistent history from API
}

function toggleNavDrawer() {
    const drawer = document.getElementById('navDrawer');
    const overlay = document.getElementById('navOverlay');

    if (drawer.classList.contains('translate-x-full')) {
        drawer.classList.remove('translate-x-full');
        overlay.classList.remove('hidden');
    } else {
        drawer.classList.add('translate-x-full');
        overlay.classList.add('hidden');
    }
}

