document.addEventListener('DOMContentLoaded', () => {
    // Poll for stats
    setInterval(fetchStats, 5000);
});

async function fetchStats() {
    try {
        const response = await fetch('/api/v1/admin/dashboard/stats');
        const data = await response.json();
        document.getElementById('online-users').textContent = data.online_users;
    } catch (error) {
        console.error('Error fetching stats:', error);
    }
}
