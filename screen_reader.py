import pyautogui
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import os
import datetime
from groq import Groq
from config import GROQ_API_KEY, MODEL_NAME
import base64
import httpx

# ============================================================
# TESSERACT PATH
# ============================================================

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

client = Groq(api_key=GROQ_API_KEY)

# ============================================================
# TAKE SCREENSHOT
# ============================================================

def take_screenshot(save=True):
    screenshot = pyautogui.screenshot()
    if save:
        path = os.path.expanduser("~/Desktop/ai_screenshot.png")
        screenshot.save(path)
        print(f"Screenshot saved: {path}")
    return screenshot


# ============================================================
# READ TEXT FROM SCREEN (OCR)
# ============================================================

def read_screen_text():
    try:
        screenshot = take_screenshot(save=False)

        # Enhance image for better OCR
        enhanced = screenshot.convert("L")
        enhanced = ImageEnhance.Contrast(enhanced).enhance(2.0)
        enhanced = enhanced.filter(ImageFilter.SHARPEN)

        # Extract text
        text = pytesseract.image_to_string(enhanced)
        text = text.strip()

        if text:
            return text
        else:
            return "No text found on screen"

    except Exception as e:
        return f"Screen reading error: {str(e)}"


# ============================================================
# READ SPECIFIC REGION OF SCREEN
# ============================================================

def read_screen_region(x, y, width, height):
    try:
        screenshot = pyautogui.screenshot(region=(x, y, width, height))
        text = pytesseract.image_to_string(screenshot)
        return text.strip()
    except Exception as e:
        return f"Region reading error: {str(e)}"


# ============================================================
# AI ANALYZES SCREENSHOT
# ============================================================

def ai_analyze_screen(user_question="What do you see on my screen?"):
    try:
        # Take screenshot
        screenshot = take_screenshot(save=True)
        path = os.path.expanduser("~/Desktop/ai_screenshot.png")

        # Convert to base64
        with open(path, "rb") as img_file:
            image_data = base64.b64encode(img_file.read()).decode("utf-8")

        # Also read text with OCR as backup
        screen_text = read_screen_text()

        # Send to AI with screen text context
        prompt = f"""The user asked: {user_question}

Here is the text currently visible on the user's screen (extracted via OCR):
{screen_text[:3000]}

Based on this screen content, please answer the user's question helpfully.
If you can see error messages, help fix them.
If you can see text, summarize or explain it.
Be specific and helpful."""

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=1024,
            temperature=0.7
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"Screen analysis error: {str(e)}"


# ============================================================
# SMART SCREEN COMMANDS
# ============================================================

def handle_screen_command(user_message):
    message_lower = user_message.lower()

    # Read all text on screen
    if any(word in message_lower for word in [
        "read screen", "what is on screen", "read my screen",
        "what does screen say", "read this"
    ]):
        text = read_screen_text()
        return f"📄 Text on your screen:\n\n{text}"

    # AI analyzes screen
    elif any(word in message_lower for word in [
        "what do you see", "analyze screen", "look at screen",
        "what is on my screen", "describe screen",
        "explain this screen", "what is this",
        "help me with this screen", "read this error"
    ]):
        return ai_analyze_screen(user_message)

    # Take screenshot only
    elif any(word in message_lower for word in [
        "take screenshot", "screenshot", "capture screen",
        "take a picture of screen"
    ]):
        take_screenshot(save=True)
        return "📸 Screenshot saved to your Desktop!"

    return None


# ============================================================
# DETECT SCREEN COMMAND
# ============================================================

def is_screen_command(user_message):
    screen_keywords = [
        "screen", "screenshot", "what do you see",
        "what is on", "read this", "analyze",
        "describe", "look at", "this error",
        "what does it say", "read my screen",
        "explain this", "what is this page"
    ]
    message_lower = user_message.lower()
    return any(keyword in message_lower for keyword in screen_keywords)