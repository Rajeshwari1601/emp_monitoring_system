import threading
import time
import io
import logging
import websocket
import mss
import pyautogui
from PIL import Image

# Configure logging
logger = logging.getLogger("ScreenStreamer")

class ScreenStreamer(threading.Thread):
    def __init__(self, api_base_url, token, screen_lock):
        super().__init__()
        self.screen_lock = screen_lock # Store lock
        self.daemon = True # Daemon thread ensuring it dies with main process
        
        # Convert http(s) -> ws(s)
        if api_base_url.startswith("https"):
            ws_url = api_base_url.replace("https", "wss")
        else:
            ws_url = api_base_url.replace("http", "ws")
            
        # Append token to query param
        self.ws_url = f"{ws_url}/ws/live?token={token}"
        self.running = False
        self.ws = None
        self.sct = mss.mss()

    def run(self):
        self.running = True
        logger.info(f"Screen streamer thread started. Target: {self.ws_url}")
        
        while self.running:
            try:
                self._connect_and_stream()
            except Exception as e:
                logger.error(f"Streamer connection error: {e}")
                time.sleep(5) # Retry delay

    def stop(self):
        self.running = False
        if self.ws:
            self.ws.close()
        logger.info("Screen streamer stopping...")

    def _connect_and_stream(self):
        # Using websocket-client synchronous interface
        self.ws = websocket.create_connection(self.ws_url)
        logger.info("WebSocket connected")
        
        # Monitor Loop
        width = 800 # Max width
        quality = 50 # JPEG Quality

        while self.running:
            start_time = time.time()
            
            try:
                # Capture Logic (MSS first, Fallback to PyAutoGUI)
                img = self._capture_screen()
                
                if not img:
                    time.sleep(1)
                    continue

                # Optimize
                # Resize if needed (PIL thumbnail is fast)
                if img.width > width:
                    img.thumbnail((width, int(width * img.height / img.width)))

                # Compress to JPEG
                with io.BytesIO() as buffer:
                    img.save(buffer, format="JPEG", quality=quality)
                    img_bytes = buffer.getvalue()
                
                # Send
                self.ws.send_binary(img_bytes)
                
                # Rate Limit (10 FPS = 0.1s)
                elapsed = time.time() - start_time
                # Ensure at least 10ms sleep to prevent lock starvation of other threads
                time.sleep(max(0.01, 0.1 - elapsed))

            except (BrokenPipeError, websocket.WebSocketConnectionClosedException, OSError):
                logger.warning("WebSocket connection lost/aborted.")
                raise # Break inner loop to trigger reconnect
            except Exception as e:
                logger.error(f"Frame error: {e}")
                time.sleep(1)

    def _capture_screen(self):
        try:
            with self.screen_lock:
                # MSS Capture
                monitor = self.sct.monitors[1] # Primary monitor
                sct_img = self.sct.grab(monitor)
                return Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        except Exception as e:
            # Fallback
            # logger.debug(f"MSS failed ({e}), using pyautogui fallback")
            try:
                with self.screen_lock:
                    return pyautogui.screenshot()
            except Exception as ex:
                logger.error(f"Capture failed: {ex}")
                return None

# Helper to start service easily
def start_stream_service(api_base_url, token, screen_lock):
    streamer = ScreenStreamer(api_base_url, token, screen_lock)
    streamer.start()
    return streamer