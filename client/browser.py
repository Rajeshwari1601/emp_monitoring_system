import win32gui
import logging
import time
from datetime import datetime
from config import BrowserConfig

logger = logging.getLogger("BrowserScanner")

def custom_find_all(control, predicate, depth=0, max_depth=BrowserConfig.MAX_SEARCH_DEPTH):
    """
    Recursively find all descendant controls matching the predicate.
    Workaround for missing FindAll method in some uiautomation versions.
    """
    results = []
    if depth > max_depth:
        return results
    
    try:
        children = control.GetChildren()
        for child in children:
            if predicate(child):
                results.append(child)
            
            # Recursively search
            results.extend(custom_find_all(child, predicate, depth + 1, max_depth))
    except Exception as e:
        # Some controls might not allow GetChildren or have access issues
        pass
        
    return results

def extract_url_from_browser_window(window, browser_name):
    """
    Attempt to extract URL from browser window using UI Automation.
    Returns URL string if found, None otherwise.
    """
    try:
        import uiautomation as auto
        
        # Strategy 1: Find Edit control with URL-like value
        # Using custom recursive search
        try:
            edits = custom_find_all(
                window, 
                lambda c: c.ControlTypeName in ['EditControl', 'ComboBoxControl'], 
                max_depth=BrowserConfig.MAX_SEARCH_DEPTH
            )
            
            for edit in edits:
                # Some controls might require specific pattern access
                value = None
                if hasattr(edit, 'GetValuePattern'):
                    p = edit.GetValuePattern()
                    if p: value = p.Value
                
                # If no pattern value, try Name as fallback for some URL bars
                if not value:
                    value = edit.Name

                if value and ('http://' in value or 'https://' in value or '.com' in value or '.org' in value):
                    return value
        except Exception:
            pass
        
        # Strategy 2: Check window name for URL patterns
        window_name = window.Name
        if window_name and ('http://' in window_name or 'https://' in window_name):
             # Extract URL from window title
             for part in window_name.split(' - '):
                 if 'http://' in part or 'https://' in part:
                     return part.strip()
        
        return None
    except Exception as e:
        logger.debug(f"URL extraction failed for {browser_name}: {e}")
        return None

def get_active_browsers():
    """
    Scans for open browsers and gets ALL tabs using UI Automation.
    Returns structured data with tab details including URLs and timestamps.
    """
    logger.debug("get_active_browsers() CALLED")
    browsers = {} 
    youtube_open = False
    current_time = datetime.now().isoformat()
    
    try:
        import uiautomation as auto
        auto.SetGlobalSearchTimeout(BrowserConfig.UI_SEARCH_TIMEOUT_MS / 1000) # helper takes seconds
        
        desktop = auto.GetRootControl()
        
        # Find all top-level windows
        windows = desktop.GetChildren()
        
        for window in windows:
            if not window.ClassName and not window.Name:
                continue

            # Identify Browser
            browser_name = None
            browser_config = None
            
            for b_name, config in BrowserConfig.BROWSERS.items():
                if config['class_name'] == window.ClassName:
                    # Check name pattern to filter out other apps with same class (e.g. Electron apps)
                    # Note: We loosen the check slightly to catch popups, but main window usually has name
                    if config['name_pattern'] in window.Name or 'chrome' in window.Name.lower() or 'edge' in window.Name.lower() or 'firefox' in window.Name.lower():
                         browser_name = b_name
                         browser_config = config
                         break
            
            if not browser_name:
                continue

            logger.debug(f"Processing {browser_name} window: {window.Name}")
            
            # Extract generic window URL (probably active tab)
            window_url = extract_url_from_browser_window(window, browser_name)
            
            tabs_found = []
            
            # Find Tabs using recursive search
            try:
                # Look for TabItemControl
                tabs = custom_find_all(
                    window, 
                    lambda c: c.ControlTypeName == 'TabItemControl', 
                    max_depth=12 # Increased depth for complex UIs
                )
                
                # If no TabItems, try finding Buttons that look like tabs (fallback)
                if not tabs:
                     btns = custom_find_all(
                         window,
                         lambda c: c.ControlTypeName == 'ButtonControl',
                         max_depth=8
                     )
                     # Filter buttons based on config
                     for btn in btns:
                         name = btn.Name
                         if name and len(name) > 2 and not any(p in name.lower() for p in BrowserConfig.EXCLUDED_BUTTON_PATTERNS):
                              # Treat as potential tab
                              tabs.append(btn)

                # Process found controls
                seen_titles = set()
                
                for tab in tabs:
                    title = tab.Name
                    if not title: continue
                    
                    # Clean title
                    clean = title
                    if browser_config:
                        clean = clean.replace(browser_config['suffix'], "")
                    
                    # Dedup
                    if clean in seen_titles: continue
                    seen_titles.add(clean)
                    
                    # Skip empty or trivial titles
                    if len(clean) < 2: continue

                    # Construct tab object
                    # Note: Detecting which tab corresponds to 'window_url' is hard.
                    # We usually assume active tab has the URL.
                    # For now, we set URL to None for non-active tabs unless we can extract it from the tab object itself (rare)
                    
                    # Heuristic: If tab title matches window title (minus suffix), it's likely the active one
                    is_active = clean in window.Name
                    tab_url = window_url if is_active else None
                    
                    tab_obj = {
                        "title": clean,
                        "url": tab_url,
                        "timestamp": current_time,
                        "browser": browser_name
                    }
                    tabs_found.append(tab_obj)
                    
                    if "youtube" in clean.lower():
                        youtube_open = True

            except Exception as e:
                logger.error(f"Error extracting tabs for {browser_name}: {e}")

            # Fallback if no tabs found: Use window title as single tab
            if not tabs_found:
                win_name = window.Name
                clean = win_name
                if browser_config:
                     clean = clean.replace(browser_config['suffix'], "")
                
                tab_obj = {
                    "title": f"[Active] {clean}",
                    "url": window_url,
                    "timestamp": current_time,
                    "browser": browser_name
                }
                tabs_found.append(tab_obj)
                if "youtube" in clean.lower():
                    youtube_open = True
            
            if browser_name not in browsers:
                browsers[browser_name] = []
            browsers[browser_name].extend(tabs_found)

    except ImportError:
        logger.warning("uiautomation not installed. Using basic detection.")
        return get_active_browsers_basic()
    except Exception as e:
        logger.error(f"UIA Error: {e}. Falling back.")
        return get_active_browsers_basic()
    
    if not browsers:
        return get_active_browsers_basic()

    return browsers, youtube_open

def get_active_browsers_basic():
    """Fallback: win32gui implementation"""
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
            clean_title = title
            
            for browser, config in BrowserConfig.BROWSERS.items():
                if config['suffix'].lower() in lower_title:
                    browser_name = browser
                    clean_title = title.replace(config['suffix'], "")
                    break
            
            if browser_name:
                if browser_name not in browsers:
                    browsers[browser_name] = []
                
                tab_obj = {
                    "title": clean_title,
                    "url": None,
                    "timestamp": current_time,
                    "browser": browser_name
                }
                browsers[browser_name].append(tab_obj)

            if "youtube" in lower_title:
                youtube_open = True
    
    try:
        win32gui.EnumWindows(enum_window_callback, None)
    except Exception as e:
        pass
        
    return browsers, youtube_open
