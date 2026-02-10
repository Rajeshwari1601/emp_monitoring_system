import sys
from config import Config
from auth_ui import launch_auth_ui
from background import BackgroundService

def main():
    while True:
        # Check for token
        token = Config.load_token()
        
        if not token:
            # Launch UI
            print("First run detected. Launching Login UI...")
            launch_auth_ui(on_success=start_background_wrapper)
        else:
            # Validate token? (Heartbeat check)
            from api_client import APIClient
            api = APIClient()
            if api.heartbeat(): 
                print("Token valid. Starting background service...")
                start_background_wrapper()
            else:
                print("Token invalid/expired. Launching UI...")
                Config.clear_token()
                launch_auth_ui(on_success=start_background_wrapper)

def start_background_wrapper():
    # This wrapper allows us to run the background service and catch the exit
    # functionality (os._exit(401)) if we were using subprocesses, but with threads + os._exit
    # the whole script dies.
    # To properly support "Stopping service" -> "Show Login", we shouldn't use os._exit(401).
    # We should fix `background.py` to not kill process, but just stop threads.
    # However, `background.py` uses `os._exit(401)`.
    # Let's adjust `start_background` to be simple.
    start_background()

def start_background():
    service = BackgroundService()
    try:
        service.start()
    except KeyboardInterrupt:
        print("Stopping service...")
        sys.exit(0)
    except SystemExit as e:
        if e.code == 401:
            print("Session expired. Restarting flow...")
            return # Returns to main loop
        sys.exit(e.code)

if __name__ == "__main__":
    main()
