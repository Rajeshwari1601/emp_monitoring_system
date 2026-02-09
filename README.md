# Employee Monitoring System

A comprehensive Employee Monitoring System consisting of a FastAPI Backend, a Python-based Desktop Agent, and an Admin Dashboard.

## Features

- **Desktop Agent (Python)**:
    - Runs silently in the background.
    - Captures screenshots at regular intervals.
    - Tracks active window and application usage duration.
    - Polls for and displays admin notifications.
    - Auto-syncs data with the backend.
- **Backend (FastAPI)**:
    - RESTful API for data ingestion and management.
    - JWT-based Authentication for Admins and Agents.
    - PostgreSQL for persistent storage (Users, Activity Logs, Screenshots).
    - Redis for real-time active user tracking and caching.
- **Admin Dashboard (HTML/JS)**:
    - View registered users and their status (Active/Inactive).
    - Monitor real-time active user count.
    - Send notifications to employees.
    - View activity logs and screenshots (via backend API).

## Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy (Async), PostgreSQL, Redis.
- **Agent**: Python, `requests`, `pywin32` (Active Window), `mss` (Screenshots), `tkinter` (Notifications).
- **Frontend**: Vanilla HTML, CSS, JavaScript.

## Prerequisites

- **Python 3.9+**
- **PostgreSQL** (running on port 5432)
- **Redis** (running on port 6379)

## Installation & Setup

### 1. Backend Setup

1.  Navigate to the `backend` directory:
    ```bash
    cd backend
    ```
2.  Create and activate a virtual environment:
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # Mac/Linux
    source venv/bin/activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r ../requirements.txt
    ```
4.  Configure Database:
    - Ensure PostgreSQL is running and a database named `employee_db` exists.
    - Update `app/core/config.py` if your credentials differ from default (`postgres:password`).
5.  Start the Server:
    ```bash
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```
    *Database tables will be created automatically on startup.*

### 2. Create Admin User

Run the helper script to create the initial Admin account:
```bash
# In backend/ directory, with venv activated
python create_admin.py
```
*Default credentials: `admin` / `adminpassword`*

### 3. Desktop Agent Setup

1.  Navigate to the agent source directory:
    ```bash
    cd ../employee_agent/src
    ```
2.  Run the agent:
    ```bash
    python main.py
    ```
3.  Login using employee credentials (you can create a new user via API or use the admin account for testing).

### 4. Admin Dashboard

1.  Open `frontend/login.html` in your web browser.
2.  Login with the Admin credentials.
3.  Monitor users, view stats, and send notifications.

## Project Structure

```
employee-monitoring-system/
├── backend/                # FastAPI Application
│   ├── app/
│   │   ├── api/            # API Endpoints
│   │   ├── core/           # Config & Security
│   │   ├── crud/           # Database Operations
│   │   ├── db/             # Database Connection
│   │   ├── models/         # SQLAlchemy Models
│   │   └── schemas/        # Pydantic Schemas
│   ├── uploads/            # Stored Screenshots
│   └── create_admin.py     # Admin creation script
├── employee_agent/         # Desktop Client
│   └── src/
│       ├── services/       # Monitoring Services
│       ├── api_client.py   # Backend Communication
│       └── main.py         # Entry Point
├── frontend/               # Admin UI
│   ├── css/
│   ├── js/
│   └── index.html
└── requirements.txt        # Python Dependencies
```
