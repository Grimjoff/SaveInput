from pynput import keyboard, mouse
import pandas as pd
from datetime import datetime
import psutil
import win32gui
import win32process
import time
import threading
# Create an empty DataFrame with columns "Time" and "Button"
df = pd.DataFrame(columns=["Time", "Button", "Process"])
last_input_time = time.time()
timeout = 3  # Seconds before inserting "/"
stop_event = threading.Event()

button_replacements = {
    "Button.left": "LC",  # Change left click to "LC"
    "Button.right": "RC",  # Change right click to "RC"
    "Key.space": " ",
    "Key.enter": "Enter",
    "Key.tab":"Tab",
    "Key.backspace": "<-",
    "Key.ctrl_l": "CTRL",
    "Key.alt_l": "alt",
    "Key.shift": "SH",
    "Button.x1": "M1",
    "Button.middle": "mid",
    "Key.esc": "esc"
}
# Function to log key presses with the time and key/button name
def get_active_window():
    try:
        hwnd = win32gui.GetForegroundWindow()  # Get active window handle
        _, pid = win32process.GetWindowThreadProcessId(hwnd)  # Get process ID
        process = psutil.Process(pid)  # Get process details
        return process.name()  # Return the executable name
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return "Unknown"

buffer = []
csv_file = "input_log.csv"
held_keys = set()
def transform_button_name(button):
    return button_replacements.get(button, button)
# Function to log key presses
def on_key_press(key):
    global held_keys
    try:
        button = key.char
    except AttributeError:
        button = str(key)
    button = transform_button_name(button)

    if button not in held_keys:
        held_keys.add(button)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        process = get_active_window()
        log_entry = [timestamp, button, process]
        buffer.append(log_entry)

        # If Enter is pressed, flush the buffer to CSV
        if button == 'Enter':
            df = pd.DataFrame(buffer, columns=["Time", "Button", "Process"])
            df.to_csv(csv_file, mode='a', header=not pd.io.common.file_exists(csv_file), index=False)
            buffer.clear()

def on_key_release(key):
    global held_keys
    try:
        button = key.char
    except AttributeError:
        button = str(key)
    button = transform_button_name(button)
    if button in held_keys:
        held_keys.remove(button)


# Function to log mouse clicks with the time and button
def on_click(x, y, button, pressed):
    if pressed:
        program = get_active_window()
        button_name = str(button)  # Get the button name
        button_name = transform_button_name(button_name)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Current time
        global df
        # Append new entry to the dataframe
        new_entry = pd.DataFrame([[timestamp, button_name, program]], columns=["Time", "Button", "Process"])
        # Append the new entry to the CSV without header
        new_entry.to_csv(csv_file, mode='a', header=not pd.io.common.file_exists(csv_file), index=False)


# Start keyboard and mouse listeners
keyboard_listener = keyboard.Listener(on_press=on_key_press, on_release=on_key_release)
mouse_listener = mouse.Listener(on_click=on_click, on_release=on_key_release)

keyboard_listener.start()
mouse_listener.start()

keyboard_listener.join()
mouse_listener.join()
