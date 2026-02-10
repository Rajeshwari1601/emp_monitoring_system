import requests
import logging
from config import Config

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class APIClient:
    def __init__(self):
        self.base_url = Config.API_BASE_URL
        self.token = Config.load_token()
        self.headers = {
            "Content-Type": "application/json"
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

    def set_token(self, token):
        self.token = token
        self.headers["Authorization"] = f"Bearer {token}"
        Config.save_token(token)

    def _log_request(self, method, url, payload=None):
        logger.debug(f"REQUEST {method} {url}")
        if payload:
            # Truncate long payloads like images
            log_payload = payload.copy()
            if "image_base64" in log_payload:
                log_payload["image_base64"] = "<BASE64_IMAGE_DATA_TRUNCATED>"
            logger.debug(f"PAYLOAD: {log_payload}")

    def _log_response(self, response):
        logger.debug(f"RESPONSE {response.status_code} {response.url}")
        try:
            logger.debug(f"BODY: {response.json()}")
        except:
            logger.debug(f"BODY: {response.text}")

    def login(self, email, password, device_id):
        url = f"{self.base_url}/auth/login"
        payload = {
            "email": email,
            "password": password,
            "device_id": device_id
        }
        self._log_request("POST", url, payload)
        try:
            response = requests.post(url, json=payload)
            self._log_response(response)
            response.raise_for_status()
            data = response.json()
            token = data.get("access_token")
            if token:
                self.set_token(token)
                return True, "Login successful"
            return False, "No token returned"
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False, str(e)

    def register(self, name, email, password, device_id, device_name):
        url = f"{self.base_url}/auth/register"
        payload = {
            "name": name,
            "email": email,
            "password": password,
            "device_id": device_id,
            "device_name": device_name
        }
        self._log_request("POST", url, payload)
        try:
            response = requests.post(url, json=payload)
            self._log_response(response)
            response.raise_for_status()
            return True, "Registration successful. Please login."
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            return False, str(e)

    def heartbeat(self):
        if not self.token: return False
        url = f"{self.base_url}/client/heartbeat"
        self._log_request("POST", url)
        try:
            response = requests.post(url, json={"status": "online"}, headers=self.headers)
            self._log_response(response)
            if response.status_code == 401:
                Config.clear_token()
                return False
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Heartbeat error: {e}")
            return False

    def get_commands(self):
        if not self.token: return []
        url = f"{self.base_url}/client/commands"
        self._log_request("GET", url)
        try:
            response = requests.get(url, headers=self.headers)
            self._log_response(response)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return []

    def ack_command(self, command_id, status):
        if not self.token: return
        url = f"{self.base_url}/client/command/ack"
        payload = {"command_id": command_id, "status": status}
        self._log_request("POST", url, payload)
        try:
            requests.post(url, json=payload, headers=self.headers)
        except:
            pass

    def upload_screenshot(self, command_id, image_base64):
        # NOT used currently because background.py implements explicit request logic?
        # Actually background.py was NOT updated to use this method, it inlined request.
        # But wait, I added logging here. Background.py logic needs to be updated or I should rely on print in background.py 
        # Background.py prints exceptions.
        # Let's add logging support to the manual requests in Background.py or better, move logic here?
        # Moving logic here is cleaner.
        pass
