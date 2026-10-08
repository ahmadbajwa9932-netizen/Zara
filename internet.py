from ddgs import DDGS
import requests
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from config import YOUTUBE_API_KEY

# ============================================================
# WEB SEARCH
# ============================================================

def search_web(query, max_results=3):
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "link":  r.get("href", ""),
                    "summary": r.get("body", "")
                })
        return results
    except Exception as e:
        return [{"title": "Error", "link": "", "summary": str(e)}]


# ============================================================
# READ ARTICLE CONTENT
# ============================================================

def read_article(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=8)
        soup = BeautifulSoup(response.text, "html.parser")

        # Remove scripts and styles
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        # Get main text
        paragraphs = soup.find_all("p")
        text = " ".join([p.get_text() for p in paragraphs[:10]])
        return text[:3000]
    except Exception as e:
        return f"Could not read article: {str(e)}"


# ============================================================
# YOUTUBE SEARCH
# ============================================================

def search_youtube(query, max_results=3):
    try:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        request = youtube.search().list(
            part="snippet",
            q=query,
            type="video",
            maxResults=max_results
        )
        response = request.execute()

        videos = []
        for item in response.get("items", []):
            video_id = item["id"]["videoId"]
            title    = item["snippet"]["title"]
            channel  = item["snippet"]["channelTitle"]
            thumb    = item["snippet"]["thumbnails"]["medium"]["url"]
            videos.append({
                "title":    title,
                "channel":  channel,
                "video_id": video_id,
                "url":      f"https://www.youtube.com/watch?v={video_id}",
                "thumb":    thumb
            })
        return videos
    except Exception as e:
        return [{"title": "Error", "channel": "", "video_id": "", 
                 "url": "", "thumb": ""}]


# ============================================================
# SMART DETECT — does user want internet or PC control?
# ============================================================

def needs_internet(user_message):
    internet_keywords = [
        "news", "latest", "today", "current", "what happened",
        "search", "find", "look up", "google", "youtube",
        "video", "watch", "weather", "price", "who is",
        "what is", "how to", "tell me about", "show me",
        "recent", "update", "trending", "world", "pakistan",
        "cricket", "football", "sports", "politics", "technology",
        "explain", "definition", "meaning", "tutorial"
    ]
    message_lower = user_message.lower()
    for keyword in internet_keywords:
        if keyword in message_lower:
            return True
    return False


def needs_youtube(user_message):
    youtube_keywords = [
        "youtube", "video", "watch", "show me video",
        "play video", "find video", "tutorial video",
        "music", "song", "play", "stream"
    ]
    message_lower = user_message.lower()
    for keyword in youtube_keywords:
        if keyword in message_lower:
            return True
    return False