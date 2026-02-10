import logging
import sys
import json
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.DEBUG)

# Add client directory to path
sys.path.append('client')

try:
    from browser import get_active_browsers
    print("Successfully imported get_active_browsers")
except ImportError as e:
    print(f"Failed to import browser module: {e}")
    sys.exit(1)

def test_browser_detection():
    print("\n--- Starting Browser Detection Test ---")
    start_time = datetime.now()
    
    try:
        browsers, youtube_open = get_active_browsers()
        
        duration = (datetime.now() - start_time).total_seconds()
        print(f"Scan completed in {duration:.2f} seconds")
        print(f"YouTube Open: {youtube_open}")
        
        if not browsers:
            print("No active browsers detected.")
        else:
            print(f"Detected {len(browsers)} browsers:")
            for browser_name, tabs in browsers.items():
                print(f"\nBrowser: {browser_name}")
                print(f"Tab Count: {len(tabs)}")
                
                for i, tab in enumerate(tabs):
                    if isinstance(tab, dict):
                        print(f"  Tab {i+1}:")
                        print(f"    Title: {tab.get('title')}")
                        print(f"    URL: {tab.get('url')}")
                        print(f"    Time: {tab.get('timestamp')}")
                    else:
                        print(f"  Tab {i+1}: {tab} (Old format)")
                        
        # Verify JSON serializability (important for API transport)
        try:
            json_output = json.dumps(browsers, default=str)
            print("\nJSON Serialization Check: PASS")
        except Exception as e:
            print(f"\nJSON Serialization Check: FAIL - {e}")

    except Exception as e:
        print(f"Error during execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_browser_detection()
