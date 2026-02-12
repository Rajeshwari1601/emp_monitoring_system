import time
import threading
import pyautogui
import psutil
import base64
import io
import json
import logging
import os
import requests
import win32gui
import tkinter as tk
from tkinter import font as tkfont
from datetime import datetime

from api_client import APIClient
from config import Config
from lists_apps import get_running_applications
from streamer import start_stream_service

# Setup logging for this module
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Background")

class BackgroundService:
    def __init__(self, screen_lock=None):
        self.api = APIClient()
        self.running = True
        self.screen_lock = screen_lock if screen_lock else threading.Lock()
        logger.info(f"BackgroundService initialized for user: {self.api.headers.get('Authorization')[:15]}...")

    def start(self):
        self.last_heartbeat = time.time()
        self.last_command_poll = time.time()
        
        # Start Heartbeat Thread
        threading.Thread(target=self.heartbeat_loop, daemon=True).start()
        # Start Command Polling Thread
        threading.Thread(target=self.command_loop, daemon=True).start()
        
        # Keep main thread alive and monitor health
        while self.running:
            self.check_health()
            time.sleep(5)

    def check_health(self):
        """Monitors the health of background threads."""
        now = time.time()
        # If no heartbeat for 120s, something is wrong
        if now - self.last_heartbeat > 120:
            logger.error(f"Heartbeat thread seems stuck! (Last: {now - self.last_heartbeat:.1f}s ago). Restarting...")
            os._exit(401)
        
        # If no command polling for 120s, something is wrong
        if now - self.last_command_poll > 120:
            logger.error(f"Command loop seems stuck! (Last: {now - self.last_command_poll:.1f}s ago). Restarting...")
            os._exit(500)

    def heartbeat_loop(self):
        while self.running:
            self.last_heartbeat = time.time()
            success = self.api.heartbeat()
            if not success:
               # Token likely expired or invalid
               logger.warning("Heartbeat failed (401). Stopping service.")
               self.running = False
               # We need to signal main thread to restart UI.
               # Since this is a thread, we can't easily restart UI from here directly without callbacks.
               # But setting running=False will stop other loops.
               # To be robust, we might exit the process and let a supervisor restart, 
               # or rely on `main.py` logic if we invoke a restart callback.
               # For this Python script:
               os._exit(401) # Exit with specific code that main.py could potentially listen to if it was wrapping this.
               # Actually, `main.py` calls `start_background` which blocks.
               # If we exit process, user has to restart app.
               # Better: `main.py` should loop.
            time.sleep(10)

    def command_loop(self):
        while self.running:
            self.last_command_poll = time.time()
            try:
                commands = self.api.get_commands()
                for cmd in commands:
                    # Run each command in a separate thread to avoid blocking
                    logger.info(f"Dispatching command {cmd.get('command')} to thread...")
                    threading.Thread(target=self.process_command, args=(cmd,), daemon=True).start()
            except Exception as e:
                logger.error(f"Error in command loop: {e}")
            time.sleep(5)

    def process_command(self, cmd):
        command_type = cmd.get("command")
        command_id = cmd.get("id")
        
        try:
            if command_type == "TAKE_SCREENSHOT":
                self.take_screenshot(command_id)
            elif command_type == "GET_RUNNING_APPS":
                self.get_running_apps(command_id)
            elif command_type == "GET_BROWSER_STATUS":
                self.get_browser_status(command_id)
            elif command_type == "SEND_NOTIFICATION":
                self.show_notification(cmd.get("payload", {}))
            
            # ACK Command
            self.api.ack_command(command_id, "EXECUTED")
        except Exception as e:
            logger.error(f"Error executing command {command_id}: {e}")
            self.api.ack_command(command_id, "FAILED")

    def take_screenshot(self, command_id):
        # Capture screenshot
        try:
            screenshot = pyautogui.screenshot()
            buffer = io.BytesIO()
            screenshot.save(buffer, format="PNG")
            img_str = base64.b64encode(buffer.getvalue()).decode()
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return

        url = f"{self.api.base_url}/client/screenshot/upload"
        
        payload = {
            "command_id": command_id,
            "image_base64": img_str
        } 
        
        logger.debug(f"UPLOADING SCREENSHOT to {url}")
        try:
             resp = requests.post(url, json=payload, headers=self.api.headers)
             logger.debug(f"UPLOAD RESULT: {resp.status_code} {resp.text}")
        except Exception as e:
            logger.error(f"Upload failed: {e}")

    def get_running_apps(self, command_id):
        # Get only user-visible applications (foreground apps with windows)
        apps = []
        try:
            # Use the new lists_apps functionality to get user-visible applications only
            visible_apps = get_running_applications()
            
            # Format the data for upload
            for app in visible_apps:
                apps.append({
                    "name": app['name'],
                    "pid": app['pid'],
                    "title": app['title'],
                    "exe_path": app['exe_path'],
                    "duration": app['duration'],
                    "icon": app['icon'],
                    "is_active": app.get('is_active', False)
                })
            
            logger.info(f"Found {len(apps)} user-visible applications")
        except Exception as e:
            logger.error(f"Error getting apps: {e}")
        
        # Upload
        url = f"{self.api.base_url}/client/apps/upload"
        payload = {
            "command_id": command_id,
            "apps": apps
        }
        logger.debug(f"UPLOADING APPS ({len(apps)}) to {url}")
        try:
            resp = requests.post(url, json=payload, headers=self.api.headers)
            logger.debug(f"Result: {resp.status_code}")
        except Exception as e:
            logger.error(f"App upload failed: {e}")

    def get_browser_status(self, command_id):
        """Captures browser status and tab details."""
        browsers = {}
        youtube_open = False
        method_used = "Basic"
        
        try:
            # Try enhanced detection first
            from browser import get_active_browsers
            logger.info("Attempting enhanced browser detection...")
            browsers, youtube_open = get_active_browsers()
            if browsers:
                method_used = "Enhanced"
        except Exception as e:
            logger.warning(f"Enhanced browser detection failed: {e}")

        # If enhanced failed or returned nothing, use basic win32 fallback
        if not browsers:
            logger.info("Using basic win32 fallback for browser detection...")
            browsers, youtube_open = self._get_browser_status_basic_logic()

        # Determine summary browser string
        if not browsers:
            browser_summary = "None detected"
        elif len(browsers) == 1:
            browser_summary = list(browsers.keys())[0]
        else:
            browser_summary = f"Multiple ({', '.join(browsers.keys())})"

        # Upload
        url = f"{self.api.base_url}/client/browser/upload"
        payload = {
            "command_id": command_id,
            "browser": browser_summary,
            "youtube_open": youtube_open,
            "details": {
                "sessions": browsers,
                "meta": {
                    "method": method_used,
                    "scanned_at": datetime.now().isoformat()
                }
            }
        }
        
        logger.info(f"PREPARING BROWSER PAYLOAD: {payload['browser']} - {len(browsers)} browsers in sessions")
        logger.debug(f"FULL BROWSER DETAILS: {payload['details']}")
        
        logger.info(f"UPLOADING BROWSER STATUS ({method_used}) to {url}")
        try:
            resp = requests.post(url, json=payload, headers=self.api.headers)
            logger.debug(f"Upload Result: {resp.status_code}")
        except Exception as e:
            logger.error(f"Browser upload failed: {e}")

    def _get_browser_status_basic_logic(self):
        """Helper for win32gui fallback that matches the 'sessions' format."""
        browsers = {}
        youtube_open = False
        current_time = datetime.now().isoformat()
        
        def enum_window_callback(hwnd, _):
            nonlocal youtube_open
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if not title: return
                
                lower_title = title.lower()
                browser_name = None
                
                if "chrome" in lower_title: browser_name = "Chrome"
                elif "edge" in lower_title: browser_name = "Edge"
                elif "firefox" in lower_title: browser_name = "Firefox"
                elif "brave" in lower_title: browser_name = "Brave"
                
                if browser_name:
                    if browser_name not in browsers: browsers[browser_name] = []
                    browsers[browser_name].append({
                        "title": title,
                        "url": None, # Basic detection can't get URLs
                        "timestamp": current_time,
                        "browser": browser_name
                    })
                
                if "youtube" in lower_title:
                    youtube_open = True
        
        try:
            win32gui.EnumWindows(enum_window_callback, None)
        except:
            pass
            
        return browsers, youtube_open



    def show_notification(self, payload):
        title = payload.get("title", "Notification")
        message = payload.get("message", "Message from Admin")
        
        # Use Tkinter for a custom, better-looking UI
        def show():
            root = tk.Tk()
            root.title(title)
            
            # Remove window decorations (borderless) for modern look
            root.overrideredirect(True)
            root.attributes('-topmost', True)
            
            # Simple Dark Theme
            bg_color = "#1f2937" # Gray-800
            text_color = "#f3f4f6" # Gray-100
            dataset_color = "#374151" # Gray-700
            blue_color = "#2563eb" # Blue-600
            
            root.configure(bg=bg_color)
            
            # Dimensions
            w = 400
            h = 250
            
            # Center on screen
            ws = root.winfo_screenwidth()
            hs = root.winfo_screenheight()
            x = (ws/2) - (w/2)
            y = (hs/2) - (h/2)
            root.geometry('%dx%d+%d+%d' % (w, h, x, y))
            
            # add shadow/border effect (simple border frame)
            frame = tk.Frame(root, bg=bg_color, highlightbackground="#4b5563", highlightthickness=2)
            frame.pack(fill=tk.BOTH, expand=True)

            # Title
            lbl_title = tk.Label(frame, text=title, bg=bg_color, fg=blue_color, font=("Segoe UI", 16, "bold"), pady=15)
            lbl_title.pack(fill=tk.X)
            
            # Message
            lbl_msg = tk.Label(frame, text=message, bg=bg_color, fg=text_color, font=("Segoe UI", 11), wraplength=350, justify=tk.CENTER)
            lbl_msg.pack(expand=True, fill=tk.BOTH, padx=20)
            
            # Close Button
            def close_win():
                root.destroy()
                
            btn = tk.Button(frame, text="ACKNOWLEDGE", command=close_win, bg=blue_color, fg="white", 
                           font=("Segoe UI", 10, "bold"), relief=tk.FLAT, activebackground="#1d4ed8", activeforeground="white",
                           cursor="hand2", padx=20, pady=8)
            btn.pack(pady=20)
            
            # focus
            root.focus_force()
            root.mainloop()
            
        threading.Thread(target=show, daemon=True).start()
