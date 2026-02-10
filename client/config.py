import os
import uuid
import platform
import subprocess

class Config:
    API_BASE_URL = "http://localhost:8000/api/v1"
    TOKEN_FILE = "client_token.key"
    
    @staticmethod
    def get_device_id():
        # Try to get UUID from WMIC
        try:
             output = subprocess.check_output('wmic csproduct get uuid', shell=True)
             return output.decode().split('\n')[1].strip()
        except:
             # Fallback to a generated/stored UUID or MAC address if WMIC fails
             # For MVP, let's use a persistent file method or mac address
             # Simple fallback:
             return str(uuid.getnode())

    @staticmethod
    def get_device_name():
        return platform.node()

    @staticmethod
    def save_token(token_data):
        with open(Config.TOKEN_FILE, "w") as f:
            # In prod, encrypt this
            f.write(token_data)

    @staticmethod
    def load_token():
        if os.path.exists(Config.TOKEN_FILE):
            with open(Config.TOKEN_FILE, "r") as f:
                return f.read().strip()
        return None

    @staticmethod
    def clear_token():
        if os.path.exists(Config.TOKEN_FILE):
            os.remove(Config.TOKEN_FILE)
