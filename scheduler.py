import threading
import time
import datetime
import re
from plyer import notification
import os

# ============================================================
# TASK STORAGE
# ============================================================

scheduled_tasks = []
task_id_counter = 0

# ============================================================
# TASK CLASS
# ============================================================

class ScheduledTask:
    def __init__(self, task_id, description, action, delay_seconds, repeat=False, repeat_interval=None):
        self.task_id        = task_id
        self.description    = description
        self.action         = action
        self.delay_seconds  = delay_seconds
        self.repeat         = repeat
        self.repeat_interval = repeat_interval
        self.created_at     = datetime.datetime.now()
        self.execute_at     = datetime.datetime.now() + datetime.timedelta(seconds=delay_seconds)
        self.cancelled      = False
        self.status         = "pending"

    def time_remaining(self):
        remaining = (self.execute_at - datetime.datetime.now()).total_seconds()
        if remaining <= 0:
            return "executing soon"
        minutes = int(remaining // 60)
        seconds = int(remaining % 60)
        if minutes > 0:
            return f"{minutes}m {seconds}s"
        return f"{seconds}s"


# ============================================================
# SHOW NOTIFICATION
# ============================================================

def show_notification(title, message):
    try:
        notification.notify(
            title=title,
            message=message,
            app_name="AI Assistant",
            timeout=10
        )
    except Exception as e:
        print(f"Notification error: {str(e)}")


# ============================================================
# SCHEDULE A TASK
# ============================================================

def schedule_task(description, action_func, delay_seconds,
                  repeat=False, repeat_interval=None):
    global task_id_counter
    task_id_counter += 1

    task = ScheduledTask(
        task_id=task_id_counter,
        description=description,
        action=action_func,
        delay_seconds=delay_seconds,
        repeat=repeat,
        repeat_interval=repeat_interval
    )

    scheduled_tasks.append(task)

    # Start timer thread
    thread = threading.Thread(
        target=run_task,
        args=(task,),
        daemon=True
    )
    thread.start()

    return task


# ============================================================
# RUN TASK
# ============================================================

def run_task(task):
    try:
        time.sleep(task.delay_seconds)

        if task.cancelled:
            task.status = "cancelled"
            return

        task.status = "executing"
        task.action()
        task.status = "completed"

        # If repeating reschedule
        if task.repeat and task.repeat_interval and not task.cancelled:
            time.sleep(task.repeat_interval)
            if not task.cancelled:
                task.execute_at = datetime.datetime.now() + \
                    datetime.timedelta(seconds=task.repeat_interval)
                task.status = "pending"
                run_task(task)

    except Exception as e:
        task.status = "error"
        print(f"Task error: {str(e)}")


# ============================================================
# CANCEL TASK
# ============================================================

def cancel_task(task_id):
    for task in scheduled_tasks:
        if task.task_id == task_id:
            task.cancelled = True
            task.status = "cancelled"
            return f"Task #{task_id} cancelled"
    return f"Task #{task_id} not found"


# ============================================================
# GET ALL TASKS
# ============================================================

def get_all_tasks():
    return [t for t in scheduled_tasks if t.status != "cancelled"]


def get_pending_tasks():
    return [t for t in scheduled_tasks if t.status == "pending"]


# ============================================================
# PARSE TIME FROM USER MESSAGE
# ============================================================

def parse_time(message):
    message_lower = message.lower()

    # Pattern: "in X minutes"
    match = re.search(r'in (\d+)\s*minute', message_lower)
    if match:
        return int(match.group(1)) * 60

    # Pattern: "in X hours"
    match = re.search(r'in (\d+)\s*hour', message_lower)
    if match:
        return int(match.group(1)) * 3600

    # Pattern: "in X seconds"
    match = re.search(r'in (\d+)\s*second', message_lower)
    if match:
        return int(match.group(1))

    # Pattern: "at HH:MM" or "at H:MM am/pm"
    match = re.search(r'at (\d{1,2}):(\d{2})\s*(am|pm)?', message_lower)
    if match:
        hour   = int(match.group(1))
        minute = int(match.group(2))
        period = match.group(3)

        if period == "pm" and hour != 12:
            hour += 12
        elif period == "am" and hour == 12:
            hour = 0

        now = datetime.datetime.now()
        target = now.replace(hour=hour, minute=minute, second=0)

        if target < now:
            target += datetime.timedelta(days=1)

        return int((target - now).total_seconds())

    # Pattern: "at Xam" or "at Xpm"
    match = re.search(r'at (\d{1,2})\s*(am|pm)', message_lower)
    if match:
        hour   = int(match.group(1))
        period = match.group(2)

        if period == "pm" and hour != 12:
            hour += 12
        elif period == "am" and hour == 12:
            hour = 0

        now = datetime.datetime.now()
        target = now.replace(hour=hour, minute=0, second=0)

        if target < now:
            target += datetime.timedelta(days=1)

        return int((target - now).total_seconds())

    return None


# ============================================================
# PARSE REPEAT INTERVAL
# ============================================================

def parse_repeat(message):
    message_lower = message.lower()
    if "every day" in message_lower or "daily" in message_lower:
        return 86400  # 24 hours
    if "every hour" in message_lower or "hourly" in message_lower:
        return 3600
    if "every 30 minutes" in message_lower:
        return 1800
    if "every 15 minutes" in message_lower:
        return 900
    return None


# ============================================================
# DETECT SCHEDULE COMMAND
# ============================================================

def is_schedule_command(message):
    keywords = [
        "remind me", "reminder", "schedule",
        "every day", "daily", "every morning",
        "every night", "every hour", "after",
        "set alarm", "alarm", "notify me",
        "in 5 minutes", "in 10 minutes",
        "in 30 minutes", "in 1 hour",
        "at 8am", "at 9am", "at 10pm",
        "every night", "automatically"
    ]
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in keywords)


# ============================================================
# HANDLE SCHEDULE COMMAND
# ============================================================

def handle_schedule_command(message, callback=None):
    message_lower = message.lower()

    # Cancel task
    if "cancel" in message_lower or "stop" in message_lower:
        match = re.search(r'#?(\d+)', message_lower)
        if match:
            task_id = int(match.group(1))
            result = cancel_task(task_id)
            return result
        return "Please specify task number to cancel. Example: cancel task #1"

    # Show all tasks
    if "show tasks" in message_lower or "list tasks" in message_lower or \
       "my tasks" in message_lower or "scheduled tasks" in message_lower:
        tasks = get_pending_tasks()
        if not tasks:
            return "No scheduled tasks right now."
        result = "📋 Your Scheduled Tasks:\n\n"
        for t in tasks:
            result += f"#{t.task_id} — {t.description}\n"
            result += f"       ⏰ Time remaining: {t.time_remaining()}\n"
            result += f"       🔄 Repeat: {'Yes' if t.repeat else 'No'}\n\n"
        return result

    # Parse time
    delay = parse_time(message)
    if not delay:
        return "Could not understand the time. Try: 'remind me in 10 minutes' or 'remind me at 5:30pm'"

    # Parse repeat
    repeat_interval = parse_repeat(message)
    is_repeat = repeat_interval is not None

    # Figure out what to do
    # Reminder (just notification)
    if "remind" in message_lower or "reminder" in message_lower or \
       "notify" in message_lower or "alarm" in message_lower:

        # Extract reminder text
        reminder_text = message
        for phrase in ["remind me to", "remind me", "reminder to",
                       "notify me to", "set alarm to", "alarm to"]:
            reminder_text = reminder_text.lower().replace(phrase, "").strip()

        # Remove time phrases
        reminder_text = re.sub(
            r'(in \d+ (minutes?|hours?|seconds?)|at \d+(:\d+)?\s*(am|pm)?|every day|daily)',
            '', reminder_text
        ).strip()

        if not reminder_text:
            reminder_text = "Your reminder!"

        def reminder_action():
            show_notification(
                "⏰ AI Assistant Reminder",
                reminder_text.capitalize()
            )
            if callback:
                callback(f"⏰ Reminder: {reminder_text.capitalize()}")

        task = schedule_task(
            description=f"Reminder: {reminder_text.capitalize()}",
            action_func=reminder_action,
            delay_seconds=delay,
            repeat=is_repeat,
            repeat_interval=repeat_interval
        )

        time_str = format_time(delay)
        repeat_str = f" (repeats daily)" if is_repeat else ""
        return f"✅ Reminder set! I will notify you in {time_str}{repeat_str}\nTask ID: #{task.task_id}"

    # PC command scheduling
    else:
        from pc_control import execute_command
        from ai_brain import ask_ai

        # Figure out what PC action to do
        action_keywords = {
            "shutdown": '{"action": "shutdown"}',
            "restart":  '{"action": "restart"}',
            "sleep":    '{"action": "sleep"}',
            "lock":     '{"action": "lock"}',
            "chrome":   '{"action": "open_app", "target": "chrome"}',
            "spotify":  '{"action": "open_app", "target": "spotify"}',
            "notepad":  '{"action": "open_app", "target": "notepad"}',
            "screenshot": '{"action": "screenshot"}',
        }

        action_command = None
        action_desc = message

        for keyword, command in action_keywords.items():
            if keyword in message_lower:
                action_command = command
                action_desc = keyword
                break

        if not action_command:
            return "Could not understand what to do. Try: 'shutdown at 11pm' or 'open chrome in 5 minutes'"

        def pc_action():
            execute_command(action_command)
            show_notification(
                "🤖 AI Assistant",
                f"Executing: {action_desc}"
            )
            if callback:
                callback(f"✅ Executed scheduled task: {action_desc}")

        task = schedule_task(
            description=f"PC Task: {action_desc}",
            action_func=pc_action,
            delay_seconds=delay,
            repeat=is_repeat,
            repeat_interval=repeat_interval
        )

        time_str = format_time(delay)
        repeat_str = f" (repeats daily)" if is_repeat else ""
        return f"✅ Scheduled! Will execute '{action_desc}' in {time_str}{repeat_str}\nTask ID: #{task.task_id}"


# ============================================================
# FORMAT TIME NICELY
# ============================================================

def format_time(seconds):
    if seconds < 60:
        return f"{int(seconds)} seconds"
    elif seconds < 3600:
        return f"{int(seconds // 60)} minutes"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        mins  = int((seconds % 3600) // 60)
        return f"{hours}h {mins}m"
    else:
        return f"{int(seconds // 86400)} days"