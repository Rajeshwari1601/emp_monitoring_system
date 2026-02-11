const api = new APIClient();
let currentUserId = null;
let commandPollInterval = null;

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

    // Load latest screenshot automatically
    loadLatestScreenshot(user.id);
}

// ------ Live Feed Management ------

function updateLiveFeed(type, data) {
    const container = document.getElementById('liveFeedContainer');
    const placeholder = document.getElementById('feedPlaceholder');
    const image = document.getElementById('feedImage');
    const list = document.getElementById('feedList');
    const loading = document.getElementById('feedLoading');
    const titleEl = document.getElementById('liveFeedTitle');
    const expandBtn = document.getElementById('expandScreenshotBtn');

    if (!container || !placeholder || !image || !list || !loading) {
        console.error("Critical elements missing for Live Feed updates");
        return;
    }

    // Reset visibility (Hide all)
    placeholder.style.display = 'none';
    image.style.display = 'none';
    list.style.display = 'none';
    loading.style.display = 'none';
    list.classList.add('hidden'); // Ensure Tailwind class is also handled if used elsewhere
    loading.classList.add('hidden');
    if (expandBtn) expandBtn.classList.add('hidden'); // Hide expand button by default

    if (type === 'reset') {
        placeholder.style.display = 'block';
        if (titleEl) titleEl.textContent = 'Live Feed';
        return;
    }

    if (type === 'loading') {
        loading.style.display = 'flex';
        loading.classList.remove('hidden');
        // Keep placeholder visible behind loading if empty
        if (!image.src || image.src.endsWith('#') || image.style.display === 'none') {
            placeholder.style.display = 'block';
        }
        return;
    }

    if (type === 'image') {
        // Set source
        image.src = data;

        // Error handling for image load
        image.onerror = function () {
            log('Error loading image. Check console.', 'error');
            console.error("Image failed to load:", data);
            placeholder.style.display = 'block'; // Fallback
            image.style.display = 'none';
            if (expandBtn) expandBtn.classList.add('hidden');
        };

        image.onload = function () {
            // Only show when loaded
            image.style.display = 'block';
            // Show expand button when image is displayed
            if (expandBtn) expandBtn.classList.remove('hidden');
        };

        // Force display block immediately too, onload handles final render
        image.style.display = 'block';

        if (titleEl) titleEl.textContent = 'Remote Screen Capture';

    } else if (type === 'apps') {
        // Redesigned structured list with Application and Duration columns
        const header = `
            <div class="flex items-center justify-between px-4 py-2 border-b border-gray-800 text-[10px] font-bold text-gray-500 uppercase tracking-wider">
                <div class="flex-1">Application</div>
                <div class="w-24 text-right">Duration</div>
            </div>
        `;

        const rows = data.map(app => {
            const name = app.name || 'Unknown';
            const icon = app.icon || 'https://placehold.co/32x32?text=?';
            const duration = app.duration || '00:00:00';

            return `
                <div class="flex items-center justify-between px-4 py-3 hover:bg-white/5 transition-colors border-b border-gray-900 last:border-0 group">
                    <div class="flex items-center flex-1 min-w-0">
                        <img src="${icon}" class="w-8 h-8 rounded p-0.5 bg-gray-800/50 mr-3 object-contain transition-transform group-hover:scale-110" 
                             onerror="this.src='https://placehold.co/32x32?text=?'">
                        <div class="truncate">
                            <div class="text-sm font-medium text-gray-200">${name}</div>
                            ${app.title ? `<div class="text-[10px] text-gray-500 truncate mt-0.5">${app.title}</div>` : ''}
                        </div>
                    </div>
                    <div class="w-24 text-right font-mono text-xs text-gray-400 group-hover:text-blue-400 transition-colors">
                        ${duration}
                    </div>
                </div>
            `;
        }).join('');

        list.innerHTML = `<div class="bg-black/40 rounded-lg overflow-hidden border border-gray-800">${header}${rows}</div>`;
        list.style.display = 'block';
        list.classList.remove('hidden');
        if (titleEl) titleEl.textContent = 'Active Applications';

    } else if (type === 'browser') {
        const status = `Browser: ${data.browser} | YouTube: ${data.youtube_open ? 'OPEN' : 'CLOSED'}`;
        list.innerHTML = `<div class="text-lg text-center mt-10">${status}</div>`;
        list.style.display = 'block';
        list.classList.remove('hidden');
        if (titleEl) titleEl.textContent = 'Browser Activity Monitoring';
    }
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
            if (attempts % 3 === 0) log(`Polling... (${attempts}/${maxAttempts})`); // Debug log

            if (type === 'TAKE_SCREENSHOT') {
                const res = await api.getScreenshot(commandId);
                if (res.url) {
                    clearInterval(commandPollInterval);
                    log(`Screenshot received!`, 'success');

                    // Display in Live Feed Container
                    // Prefer Base64 (image_data) if available to avoid CORS/Mixed Content issues
                    let imageUrl;
                    if (res.image_data) {
                        imageUrl = res.image_data;
                    } else {
                        // Fallback to URL with timestamp
                        imageUrl = `${res.url}?t=${new Date().getTime()}`;
                    }

                    updateLiveFeed('image', imageUrl);

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
            // Ignore errors while polling, but log fatal ones
            if (attempts % 5 === 0) log(`Polling error: ${e.message}`, 'warning');
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

// ------ Latest Screenshot Functions ------

async function loadLatestScreenshot(userId) {
    if (!userId) return;

    try {
        const data = await api.getLatestScreenshot(userId);

        // Prefer base64 image_data if available
        let imageUrl;
        if (data.image_data) {
            imageUrl = data.image_data;
        } else {
            // Fallback to URL with cache-busting timestamp
            imageUrl = `${data.url}?t=${new Date().getTime()}`;
        }

        // Update live feed with the screenshot
        updateLiveFeed('image', imageUrl);

        log('Latest screenshot loaded', 'success');

    } catch (err) {
        // No screenshot available - this is normal for new users
        console.log('No screenshot available:', err.message);
        // Keep the placeholder visible
        updateLiveFeed('reset');
    }
}

// Expand screenshot to fullscreen
function expandScreenshot() {
    const feedImage = document.getElementById('feedImage');
    const modal = document.getElementById('screenshotModal');
    const previewImage = document.getElementById('screenshotPreview');
    const downloadLink = document.getElementById('downloadLink');

    if (!feedImage || !feedImage.src || feedImage.style.display === 'none') {
        console.log('No screenshot to expand');
        return;
    }

    // Set the modal image to the current feed image
    if (previewImage) previewImage.src = feedImage.src;
    if (downloadLink) downloadLink.href = feedImage.src;

    // Show modal
    if (modal) {
        modal.classList.remove('hidden');
        log('Screenshot expanded to fullscreen', 'info');
    }
}

