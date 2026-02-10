# Running Apps Feature - Implementation Summary

## Overview
Successfully integrated a Windows-specific feature to track **user-visible applications** (Chrome, VS Code, Teams, File Explorer, etc.) while excluding background services and system processes.

## Files Created/Modified

### 1. **Created: `client/lists_apps.py`**
   - **Purpose**: Core module for detecting user-visible applications
   - **Key Functions**:
     - `get_running_applications()` - Returns detailed list of user-visible apps
     - `get_running_applications_simple()` - Returns simple list of process names
     - `print_running_applications()` - Formatted console output
   
   - **Filtering Logic**:
     - ✅ Checks if window is visible
     - ✅ Validates window has a title
     - ✅ Excludes tool windows (`WS_EX_TOOLWINDOW`)
     - ✅ Requires proper window styles (`WS_CAPTION`, `WS_SYSMENU`)
     - ✅ Checks taskbar presence (`WS_EX_APPWINDOW`)
     - ✅ Removes duplicate entries

   - **Returns**: List of dictionaries with:
     - `title` - Window title (e.g., "Employee Monitoring System - Chrome")
     - `process_name` - Executable name (e.g., "chrome.exe")
     - `exe_path` - Full path to executable
     - `pid` - Process ID

### 2. **Modified: `client/background.py`**
   - **Line 17**: Added import for `lists_apps` module
   - **Lines 109-140**: Updated `get_running_apps()` method to:
     - Use `get_running_applications()` instead of generic `psutil` approach
     - Send enhanced data including `title` and `exe_path`
     - Provide better logging

### 3. **Modified: `API master/app/schemas/client.py`**
   - **Lines 45-49**: Enhanced `AppInfo` schema to include:
     - `title: Optional[str]` - Window title
     - `exe_path: Optional[str]` - Executable path
   - Maintains backward compatibility with optional fields

### 4. **Modified: `admin_panel/js/app.js`**
   - **Lines 256-278**: Enhanced apps display in Live Feed:
     - Shows window title prominently
     - Displays process name as secondary info
     - Shows executable path with truncation
     - Styled cards with Tailwind CSS
     - Fallback for apps without titles

## How It Works

### 1. **Admin Panel Workflow**
   1. Admin selects a user
   2. Clicks "Running Apps" button
   3. System sends `GET_RUNNING_APPS` command to client

### 2. **Client Processing**
   1. Client receives command via polling (`background.py` line 73)
   2. Calls `get_running_apps()` method (line 110)
   3. Uses `lists_apps.get_running_applications()` to get user-visible apps
   4. Formats data and uploads to `/client/apps/upload` endpoint

### 3. **Backend Storage**
   1. API endpoint `/client/apps/upload` receives data
   2. Stores in `AppLog` database table
   3. Acknowledges command as `EXECUTED`

### 4. **Admin Panel Display**
   1. Polls for command completion
   2. Fetches app data via `api.getApps(userId)`
   3. Displays in Live Feed with enhanced UI showing:
      - Window title (primary)
      - Process name
      - Executable path

## Example Output

When running `lists_apps.py` directly:

```
Found 3 user-visible application(s):
================================================================================

1. Employee Monitoring System Summary - Google Chrome
   Process: chrome.exe (PID: 22424)
   Path: C:\Program Files\Google\Chrome\Application\chrome.exe

2. Windows Mobility Center
   Process: mblctr.exe (PID: 17004)
   Path: C:\Windows\System32\mblctr.exe

3. Chat | Pranita Patil | Microsoft Teams
   Process: ms-teams.exe (PID: 17804)
   Path: C:\Program Files\WindowsApps\MSTeams_...\ms-teams.exe
```

## Dependencies

All required dependencies already exist in `client/requirements.txt`:
- `pywin32` - Windows API access
- `psutil` - Process information

## Testing

Tested and verified:
- ✅ Module imports correctly
- ✅ Detects only user-visible applications
- ✅ Excludes background services
- ✅ Integration with background service works
- ✅ API schema supports enhanced data
- ✅ Admin panel displays enhanced information

## Notes

- **Windows-specific**: Uses `win32gui` and `win32con` APIs
- **No changes to existing features**: All modifications are additive
- **Backward compatible**: Optional fields in API schema
- **Auto-reload**: FastAPI server automatically picks up schema changes
- **Performance**: Filters at Windows API level for efficiency
