import os
import uuid
import platform
import subprocess

class Config:
    # API_BASE_URL = "https://unintruding-nehemiah-imputative.ngrok-free.dev/api/v1"
    API_BASE_URL = "http://localhost:8001/api/v1"
    TOKEN_FILE = "client_token.key"
    
    @staticmethod
    def get_device_id():
        try:
            # Use wmic but handle encoding and potential multiple lines
            output = subprocess.check_output('wmic csproduct get uuid', shell=True)
            # Try different decodings to be safe on Windows
            try:
                decoded = output.decode('utf-8')
            except:
                decoded = output.decode('cp1252', errors='ignore')
            
            lines = [l.strip() for l in decoded.split('\n') if l.strip()]
            if len(lines) > 1:
                # UUID is usually the second line (index 1) after the header 'UUID'
                uuid_str = lines[1]
                # Final check: remove any non-alphanumeric characters except hyphens
                import re
                uuid_str = re.sub(r'[^a-zA-Z0-9-]', '', uuid_str)
                return uuid_str
            return platform.node() # Fallback to hostname
        except Exception:
            # Fallback to MAC address based UUID
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
