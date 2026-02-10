import sys
import psutil
try:
    import uiautomation as auto
    print(f"Imported uiautomation version: {auto.VERSION}")
except ImportError as e:
    print(f"Failed to import uiautomation: {e}")
    sys.exit(1)

def get_process_name(pid):
    try:
        return psutil.Process(pid).name()
    except:
        return ""

def custom_find_all(control, predicate, depth=0, max_depth=5):
    results = []
    if depth > max_depth:
        return results
    
    children = control.GetChildren()
    for child in children:
        if predicate(child):
            results.append(child)
        
        # Recursively search
        results.extend(custom_find_all(child, predicate, depth + 1, max_depth))
    return results

def inspect_chrome():
    print("\nAPI Check:")
    if hasattr(auto, 'FindAll'): print(" - auto.FindAll exists")
    else: print(" - auto.FindAll DOES NOT exist")
    
    print("\nLooking for actual Google Chrome windows...")
    root = auto.GetRootControl()
    
    chrome_window = None
    for win in root.GetChildren():
        if win.ClassName == 'Chrome_WidgetWin_1':
            proc_name = get_process_name(win.ProcessId)
            if 'chrome' in proc_name.lower():
                print(f"FOUND CHROME CANDIDATE: '{win.Name}' (PID: {win.ProcessId})")
                chrome_window = win
                break

    if not chrome_window:
        print("No Chrome browser windows found!")
        return

    print(f"\nInspecting: {chrome_window.Name}")
    print("Checking available methods on window object...")
    methods = [m for m in dir(chrome_window) if not m.startswith('_')]
    print(f"Methods: {methods[:10]} ...")

    print("\nSearching for TabItemControl using custom recursive search (depth=10)...")
    # Custom search
    tabs = custom_find_all(chrome_window, lambda c: c.ControlTypeName == 'TabItemControl', max_depth=10)
    
    if not tabs:
        print("No TabItemControl found via recursive search.")
    else:
        print(f"Found {len(tabs)} tabs via recursive search:")
        for t in tabs:
             print(f" - Tab: '{t.Name}'")

if __name__ == "__main__":
    inspect_chrome()
