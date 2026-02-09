# Employee Monitoring System

This project is a comprehensive Employee Monitoring System consisting of a FastAPI backend, a Python-based Employee Agent, and a simple Admin Dashboard.

## Project Structure

### Backend (`backend/`)
The backend is built with FastAPI and handles:
- **Authentication**: JWT-based login (`api/v1/endpoints/auth.py`).
- **Activity Logging**: Receives logs from agents (`api/v1/endpoints/activity.py`).
- **Alerts**: Manages alerts via polling (`api/v1/endpoints/alerts.py`).
- **Screenshots**: Stores uploaded screenshots (`api/v1/endpoints/screenshots.py`).
- **Admin**: internal stats and management (`api/v1/endpoints/admin.py`).

**Key Files:**
- `app/main.py`: Entry point for the API.
- `app/core/config.py`: Configuration settings.

### Employee Agent (`employee_agent/`)
A background service that runs on employee machines.
- **Heartbeats**: Sends periodic signals to the backend (`src/services/heartbeat.py`).
- **Screenshots**: Captures screen content (`src/services/screenshot.py`).
- **Activity Tracking**: Monitors active windows (`src/services/activity.py`).
- **Polling**: Checks for commands from backend (`src/services/poller.py`).

**Key Files:**
- `src/main.py`: Entry point for the agent service.

### Frontend (`frontend/`)
A simple admin dashboard.
- `index.html`: Main dashboard view.
- `js/main.js`: Logic to poll backend for stats.

## Setup Instructions

1.  **Backend**:
    ```bash
    cd backend
    pip install -r requirements.txt
    uvicorn app.main:app --reload
    ```

2.  **Employee Agent**:
    ```bash
    cd employee_agent/src
    python main.py
    ```

3.  **Frontend**:
    Open `frontend/index.html` in a web browser.

## Requirements
- Python 3.8+
- PostgreSQL
- Redis
