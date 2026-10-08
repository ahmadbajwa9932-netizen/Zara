import subprocess
import os
import json
import webbrowser
import pyautogui
import psutil
import shutil
import ctypes
import platform
import screen_brightness_control as sbc
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
import math
import time
import glob

# ============================================================
# MAIN COMMAND EXECUTOR
# ============================================================

def execute_command(ai_response):
    try:
        # Handle multiple JSON commands in one response
        lines = ai_response.strip().split("\n")
        executed = False

        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                command = json.loads(line)
                action = command.get("action")

                if action == "open_app":
                    result = open_app(command.get("target"))
                    print(f"Executed: {result}")
                    executed = True
                    time.sleep(1)  # Wait for app to open

                elif action == "type_text":
                    time.sleep(2)  # Wait for app/browser to be ready
                    result = type_text(command.get("text"))
                    print(f"Executed: {result}")
                    executed = True

                elif action == "press_key":
                    time.sleep(0.5)
                    result = press_key(command.get("key"))
                    print(f"Executed: {result}")
                    executed = True

                elif action == "search_web":
                    result = search_web(command.get("query"))
                    print(f"Executed: {result}")
                    executed = True

                elif action == "open_url":
                    result = open_url(command.get("url"))
                    print(f"Executed: {result}")
                    executed = True

                elif action == "open_youtube":
                    result = open_youtube(command.get("query"))
                    print(f"Executed: {result}")
                    executed = True

                elif action == "close_app":
                    result = close_app(command.get("target"))
                    print(f"Executed: {result}")
                    executed = True

                elif action == "set_volume":
                    result = set_volume(command.get("level"))
                    print(f"Executed: {result}")
                    executed = True

                elif action == "mute":
                    result = mute_volume()
                    executed = True

                elif action == "unmute":
                    result = unmute_volume()
                    executed = True

                elif action == "set_brightness":
                    result = set_brightness(command.get("level"))
                    executed = True

                elif action == "get_battery":
                    result = get_battery()
                    print(result)
                    executed = True

                elif action == "get_system_info":
                    result = get_system_info()
                    print(result)
                    executed = True

                elif action == "shutdown":
                    result = shutdown()
                    executed = True

                elif action == "restart":
                    result = restart()
                    executed = True

                elif action == "sleep":
                    result = sleep()
                    executed = True

                elif action == "lock":
                    result = lock_pc()
                    executed = True

                elif action == "logout":
                    result = logout()
                    executed = True

                elif action == "type_text":
                    result = type_text(command.get("text"))
                    executed = True

                elif action == "press_key":
                    result = press_key(command.get("key"))
                    executed = True

                elif action == "hotkey":
                    result = hotkey(command.get("keys"))
                    executed = True

                elif action == "click":
                    result = click(command.get("x"), command.get("y"))
                    executed = True

                elif action == "scroll":
                    result = scroll(command.get("direction"), command.get("amount", 3))
                    executed = True

                elif action == "screenshot":
                    result = take_screenshot()
                    executed = True

                elif action == "copy_to_clipboard":
                    result = copy_to_clipboard(command.get("text"))
                    executed = True

                elif action == "minimize_all":
                    result = minimize_all()
                    executed = True

                elif action == "maximize_window":
                    result = maximize_window()
                    executed = True

                elif action == "close_window":
                    result = close_active_window()
                    executed = True

                elif action == "list_running_apps":
                    result = list_running_apps()
                    executed = True

                elif action == "open_file":
                    result = open_file(command.get("path"))
                    executed = True

                elif action == "delete_file":
                    result = delete_file(command.get("path"))
                    executed = True

                elif action == "create_folder":
                    result = create_folder(command.get("path"))
                    executed = True

                elif action == "copy_file":
                    result = copy_file(command.get("source"), command.get("destination"))
                    executed = True

                elif action == "move_file":
                    result = move_file(command.get("source"), command.get("destination"))
                    executed = True

                elif action == "rename_file":
                    result = rename_file(command.get("path"), command.get("new_name"))
                    executed = True

                elif action == "list_files":
                    result = list_files(command.get("path"))
                    executed = True

                elif action == "search_file":
                    result = search_file(command.get("name"))
                    executed = True

            except json.JSONDecodeError:
                continue

        return executed

    except Exception as e:
        print(f"Execute error: {str(e)}")
        return False


# ============================================================
# APP CONTROL
# ============================================================

def open_app(app_name):
    apps = {
        "chrome":           r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "google chrome":    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "firefox":          r"C:\Program Files\Mozilla Firefox\firefox.exe",
        "edge":             r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "notepad":          "notepad.exe",
        "notepad++":        r"C:\Program Files\Notepad++\notepad++.exe",
        "calculator":       "calc.exe",
        "vlc":              r"C:\Program Files\VideoLAN\VLC\vlc.exe",
        "vscode":           r"C:\Users\Lenovo\AppData\Local\Programs\Microsoft VS Code\Code.exe",
        "vs code":          r"C:\Users\Lenovo\AppData\Local\Programs\Microsoft VS Code\Code.exe",
        "explorer":         "explorer.exe",
        "file explorer":    "explorer.exe",
        "task manager":     "taskmgr.exe",
        "spotify":          r"C:\Users\Lenovo\AppData\Roaming\Spotify\Spotify.exe",
        "word":             r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
        "excel":            r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
        "powerpoint":       r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",
        "paint":            "mspaint.exe",
        "cmd":              "cmd.exe",
        "command prompt":   "cmd.exe",
        "powershell":       "powershell.exe",
        "control panel":    "control.exe",
        "snipping tool":    "snippingtool.exe",
        "wordpad":          "wordpad.exe",
        "winrar":           r"C:\Program Files\WinRAR\WinRAR.exe",
        "whatsapp":         r"C:\Users\Lenovo\AppData\Local\WhatsApp\WhatsApp.exe",
        "telegram":         r"C:\Users\Lenovo\AppData\Roaming\Telegram Desktop\Telegram.exe",
        "discord":          r"C:\Users\Lenovo\AppData\Local\Discord\app-1.0.9016\Discord.exe",
        "zoom":             r"C:\Users\Lenovo\AppData\Roaming\Zoom\bin\Zoom.exe",
    }

    try:
        app_key = app_name.lower().strip()
        
        # Check if we have a known path
        if app_key in apps:
            path = apps[app_key]
            # Check if file actually exists at that path
            if os.path.exists(path):
                subprocess.Popen([path])
                return f"Opened {app_name}"
            else:
                # File not at expected path, try searching
                return smart_find_and_open(app_name)
        else:
            return smart_find_and_open(app_name)

    except Exception as e:
        return f"Could not open {app_name}: {str(e)}"


def smart_find_and_open(app_name):
    # Common search locations
    search_paths = [
        r"C:\Program Files",
        r"C:\Program Files (x86)",
        f"C:\\Users\\Lenovo\\AppData\\Local",
        f"C:\\Users\\Lenovo\\AppData\\Roaming",
        f"C:\\Users\\Lenovo\\AppData\\Local\\Programs",
    ]

    app_lower = app_name.lower().replace(" ", "")

    for base_path in search_paths:
        try:
            for root, dirs, files in os.walk(base_path):
                for file in files:
                    if file.lower().endswith(".exe"):
                        if app_lower in file.lower():
                            full_path = os.path.join(root, file)
                            subprocess.Popen([full_path])
                            return f"Found and opened {app_name} at {full_path}"
        except:
            continue

    # Last resort — try Windows shell
    try:
        os.system(f"start {app_name}")
        return f"Attempted to open {app_name}"
    except:
        return f"Could not find {app_name} on your PC"


def close_app(app_name):
    closed = False
    for proc in psutil.process_iter(['name']):
        try:
            if app_name.lower() in proc.info['name'].lower():
                proc.kill()
                closed = True
        except:
            pass
    return f"Closed {app_name}" if closed else f"App {app_name} not found"


def list_running_apps():
    apps = []
    for proc in psutil.process_iter(['name']):
        try:
            name = proc.info['name']
            if name not in apps:
                apps.append(name)
        except:
            pass
    return "\n".join(apps[:30])


# ============================================================
# FILE MANAGEMENT
# ============================================================

def open_file(path):
    try:
        os.startfile(path)
        return f"Opened {path}"
    except Exception as e:
        return f"Error: {str(e)}"


def delete_file(path):
    try:
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
        return f"Deleted {path}"
    except Exception as e:
        return f"Error: {str(e)}"


def create_folder(path):
    try:
        os.makedirs(path, exist_ok=True)
        return f"Folder created: {path}"
    except Exception as e:
        return f"Error: {str(e)}"


def copy_file(source, destination):
    try:
        shutil.copy2(source, destination)
        return f"Copied {source} to {destination}"
    except Exception as e:
        return f"Error: {str(e)}"


def move_file(source, destination):
    try:
        shutil.move(source, destination)
        return f"Moved {source} to {destination}"
    except Exception as e:
        return f"Error: {str(e)}"


def rename_file(path, new_name):
    try:
        directory = os.path.dirname(path)
        new_path = os.path.join(directory, new_name)
        os.rename(path, new_path)
        return f"Renamed to {new_name}"
    except Exception as e:
        return f"Error: {str(e)}"


def list_files(path):
    try:
        files = os.listdir(path)
        return "\n".join(files)
    except Exception as e:
        return f"Error: {str(e)}"


def search_file(name):
    try:
        results = []
        for drive in ["C:/", "D:/", "E:/"]:
            pattern = os.path.join(drive, "**", name)
            found = glob.glob(pattern, recursive=True)
            results.extend(found[:5])
        return "\n".join(results) if results else "File not found"
    except Exception as e:
        return f"Error: {str(e)}"


# ============================================================
# BROWSER & INTERNET
# ============================================================

def search_web(query):
    url = f"https://www.google.com/search?q={query}"
    webbrowser.open(url)
    return f"Searching for: {query}"


def open_url(url):
    webbrowser.open(url)
    return f"Opened: {url}"


def open_youtube(query):
    url = f"https://www.youtube.com/results?search_query={query}"
    webbrowser.open(url)
    return f"Searching YouTube for: {query}"


# ============================================================
# SYSTEM SETTINGS
# ============================================================

def set_volume(level):
    try:
        level = int(level)
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        volume.SetMasterVolumeLevelScalar(level / 100, None)
        return f"Volume set to {level}%"
    except Exception as e:
        return f"Error: {str(e)}"


def mute_volume():
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        volume.SetMute(1, None)
        return "Volume muted"
    except Exception as e:
        return f"Error: {str(e)}"


def unmute_volume():
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        volume.SetMute(0, None)
        return "Volume unmuted"
    except Exception as e:
        return f"Error: {str(e)}"


def set_brightness(level):
    try:
        sbc.set_brightness(int(level))
        return f"Brightness set to {level}%"
    except Exception as e:
        return f"Error: {str(e)}"


def get_battery():
    try:
        battery = psutil.sensors_battery()
        if battery:
            return f"Battery: {battery.percent}% - {'Charging' if battery.power_plugged else 'Not Charging'}"
        return "No battery found"
    except Exception as e:
        return f"Error: {str(e)}"


def get_system_info():
    try:
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        return (
            f"CPU Usage   : {cpu}%\n"
            f"RAM Used    : {ram.used // (1024**2)} MB / {ram.total // (1024**2)} MB\n"
            f"Disk Used   : {disk.used // (1024**3)} GB / {disk.total // (1024**3)} GB\n"
            f"OS          : {platform.system()} {platform.release()}"
        )
    except Exception as e:
        return f"Error: {str(e)}"


# ============================================================
# POWER CONTROL
# ============================================================

def shutdown():
    os.system("shutdown /s /t 5")
    return "Shutting down in 5 seconds"

def restart():
    os.system("shutdown /r /t 5")
    return "Restarting in 5 seconds"

def sleep():
    os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
    return "Going to sleep"

def lock_pc():
    ctypes.windll.user32.LockWorkStation()
    return "PC locked"

def logout():
    os.system("shutdown /l")
    return "Logging out"


# ============================================================
# KEYBOARD & MOUSE
# ============================================================

def type_text(text):
    time.sleep(0.5)
    pyautogui.typewrite(text, interval=0.05)
    return f"Typed: {text}"

def press_key(key):
    pyautogui.press(key)
    return f"Pressed: {key}"

def hotkey(keys):
    key_list = keys.split("+")
    pyautogui.hotkey(*key_list)
    return f"Pressed hotkey: {keys}"

def click(x, y):
    pyautogui.click(int(x), int(y))
    return f"Clicked at {x}, {y}"

def scroll(direction, amount):
    if direction == "up":
        pyautogui.scroll(int(amount))
    else:
        pyautogui.scroll(-int(amount))
    return f"Scrolled {direction}"

def take_screenshot():
    path = os.path.expanduser("~/Desktop/screenshot.png")
    screenshot = pyautogui.screenshot()
    screenshot.save(path)
    return f"Screenshot saved to Desktop"


# ============================================================
# CLIPBOARD
# ============================================================

def copy_to_clipboard(text):
    pyautogui.hotkey('ctrl', 'a')
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()
    root.clipboard_clear()
    root.clipboard_append(text)
    root.update()
    root.destroy()
    return f"Copied to clipboard"

def get_clipboard():
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()
    text = root.clipboard_get()
    root.destroy()
    return f"Clipboard: {text}"


# ============================================================
# WINDOW CONTROL
# ============================================================

def minimize_all():
    pyautogui.hotkey('win', 'd')
    return "All windows minimized"

def maximize_window():
    pyautogui.hotkey('win', 'up')
    return "Window maximized"

def close_active_window():
    pyautogui.hotkey('alt', 'f4')
    return "Window closed"