import json
import os

# ============================================================
# SHORTCUTS FILE
# ============================================================

SHORTCUTS_FILE = "shortcuts.json"

# ============================================================
# LOAD & SAVE
# ============================================================

def load_shortcuts():
    if os.path.exists(SHORTCUTS_FILE):
        try:
            with open(SHORTCUTS_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_shortcuts(shortcuts):
    with open(SHORTCUTS_FILE, "w") as f:
        json.dump(shortcuts, f, indent=4)


# ============================================================
# ADD SHORTCUT
# ============================================================

def add_shortcut(name, commands):
    shortcuts = load_shortcuts()
    shortcuts[name.lower().strip()] = {
        "name": name,
        "commands": commands,
        "created_at": str(__import__('datetime').datetime.now())
    }
    save_shortcuts(shortcuts)
    return f"✅ Shortcut '{name}' saved successfully!"


# ============================================================
# DELETE SHORTCUT
# ============================================================

def delete_shortcut(name):
    shortcuts = load_shortcuts()
    key = name.lower().strip()
    if key in shortcuts:
        del shortcuts[key]
        save_shortcuts(shortcuts)
        return f"✅ Shortcut '{name}' deleted!"
    return f"❌ Shortcut '{name}' not found."


# ============================================================
# GET SHORTCUT
# ============================================================

def get_shortcut(name):
    shortcuts = load_shortcuts()
    return shortcuts.get(name.lower().strip())


# ============================================================
# LIST ALL SHORTCUTS
# ============================================================

def list_shortcuts():
    shortcuts = load_shortcuts()
    if not shortcuts:
        return "No shortcuts saved yet."

    result = "⚡ Your Custom Shortcuts:\n\n"
    for key, data in shortcuts.items():
        result += f"🔹 '{data['name']}'\n"
        result += f"   Commands: {len(data['commands'])} steps\n"
        for i, cmd in enumerate(data['commands']):
            result += f"   Step {i+1}: {cmd}\n"
        result += "\n"
    return result


# ============================================================
# EXECUTE SHORTCUT
# ============================================================

def execute_shortcut(name, callback=None):
    shortcut = get_shortcut(name)
    if not shortcut:
        return False

    from pc_control import execute_command
    import time

    commands = shortcut["commands"]
    results = []

    for i, command in enumerate(commands):
        try:
            # It is a JSON PC command
            if command.strip().startswith("{"):
                execute_command(command)
                results.append(f"✅ Step {i+1} done")
                time.sleep(1)

            # It is a plain text AI command
            else:
                from ai_brain import ask_ai
                response = ask_ai(command)
                execute_command(response)
                results.append(f"✅ Step {i+1} done")
                time.sleep(1)

        except Exception as e:
            results.append(f"❌ Step {i+1} failed: {str(e)}")

    if callback:
        callback(f"⚡ Shortcut '{name}' completed!\n" + "\n".join(results))

    return True


# ============================================================
# DETECT SHORTCUT COMMANDS
# ============================================================

def is_shortcut_command(message):
    keywords = [
        "save shortcut", "create shortcut", "add shortcut",
        "delete shortcut", "remove shortcut",
        "show shortcuts", "list shortcuts", "my shortcuts",
        "run shortcut", "execute shortcut"
    ]
    message_lower = message.lower()

    # Check keywords
    if any(k in message_lower for k in keywords):
        return True

    # Check if message matches a saved shortcut name
    shortcuts = load_shortcuts()
    for key in shortcuts:
        if key in message_lower:
            return True

    return False


# ============================================================
# HANDLE SHORTCUT COMMAND
# ============================================================

def handle_shortcut_command(message, callback=None):
    message_lower = message.lower().strip()

    # Show all shortcuts
    if any(k in message_lower for k in [
        "show shortcuts", "list shortcuts", "my shortcuts"
    ]):
        return list_shortcuts()

    # Delete shortcut
    if any(k in message_lower for k in ["delete shortcut", "remove shortcut"]):
        name = message_lower
        for phrase in ["delete shortcut", "remove shortcut"]:
            name = name.replace(phrase, "").strip()
        return delete_shortcut(name)

    # Save new shortcut
    # Format: save shortcut "work mode" = open chrome, open vscode
    if any(k in message_lower for k in ["save shortcut", "create shortcut", "add shortcut"]):
        try:
            # Extract name between quotes
            import re
            name_match = re.search(r'["\'](.+?)["\']', message)
            if not name_match:
                return (
                    "Please use this format:\n"
                    "save shortcut 'work mode' = open chrome, open vscode, open notepad"
                )

            name = name_match.group(1)

            # Extract commands after =
            if "=" not in message:
                return (
                    "Please use this format:\n"
                    "save shortcut 'work mode' = open chrome, open vscode"
                )

            commands_part = message.split("=", 1)[1].strip()

            # Split by comma
            raw_commands = [c.strip() for c in commands_part.split(",")]

            # Convert to JSON commands
            commands = []
            app_map = {
                "open chrome":      '{"action": "open_app", "target": "chrome"}',
                "open firefox":     '{"action": "open_app", "target": "firefox"}',
                "open edge":        '{"action": "open_app", "target": "edge"}',
                "open notepad":     '{"action": "open_app", "target": "notepad"}',
                "open vscode":      '{"action": "open_app", "target": "vscode"}',
                "open vs code":     '{"action": "open_app", "target": "vscode"}',
                "open spotify":     '{"action": "open_app", "target": "spotify"}',
                "open calculator":  '{"action": "open_app", "target": "calculator"}',
                "open explorer":    '{"action": "open_app", "target": "explorer"}',
                "screenshot":       '{"action": "screenshot"}',
                "take screenshot":  '{"action": "screenshot"}',
                "minimize all":     '{"action": "minimize_all"}',
                "lock pc":          '{"action": "lock"}',
                "lock":             '{"action": "lock"}',
                "shutdown":         '{"action": "shutdown"}',
                "restart":          '{"action": "restart"}',
                "sleep":            '{"action": "sleep"}',
                "mute":             '{"action": "mute"}',
                "unmute":           '{"action": "unmute"}',
            }

            # Volume/brightness patterns
            import re
            for raw in raw_commands:
                raw_lower = raw.lower().strip()
                matched = False

                # Check app map
                for key, cmd in app_map.items():
                    if key in raw_lower:
                        commands.append(cmd)
                        matched = True
                        break

                # Volume pattern
                if not matched:
                    vol = re.search(r'volume\s+(\d+)', raw_lower)
                    if vol:
                        commands.append(
                            f'{{"action": "set_volume", "level": {vol.group(1)}}}'
                        )
                        matched = True

                # Brightness pattern
                if not matched:
                    bright = re.search(r'brightness\s+(\d+)', raw_lower)
                    if bright:
                        commands.append(
                            f'{{"action": "set_brightness", "level": {bright.group(1)}}}'
                        )
                        matched = True

                # Keep as plain text if not matched
                if not matched:
                    commands.append(raw)

            if not commands:
                return "No valid commands found. Please check your shortcut format."

            return add_shortcut(name, commands)

        except Exception as e:
            return f"Error saving shortcut: {str(e)}"

    # Run shortcut — check if message matches any saved shortcut
    shortcuts = load_shortcuts()
    for key in shortcuts:
        if key in message_lower:
            def run():
                execute_shortcut(key, callback=callback)
            import threading
            threading.Thread(target=run, daemon=True).start()
            return f"⚡ Running shortcut '{key}'..."

    return "Shortcut command not understood. Try: 'show shortcuts' or 'save shortcut \"work mode\" = open chrome, open vscode'"