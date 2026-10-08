from groq import Groq
from config import GROQ_API_KEY, MODEL_NAME
from internet import search_web, read_article, needs_internet, needs_youtube, search_youtube

client = Groq(api_key=GROQ_API_KEY)

conversation_history = [
    {
        "role": "system",
        "content": """You are an intelligent AI assistant that controls a Windows 10 PC.
You can open apps, manage files, search the internet, play YouTube videos,
control system settings, and answer any question.

When the user wants to control the PC, respond ONLY in this exact JSON format:
{"action": "open_app", "target": "chrome"}
{"action": "search_web", "query": "AI news today"}
{"action": "set_volume", "level": 50}
{"action": "shutdown"}
{"action": "open_file", "path": "C:/Users/file.txt"}
{"action": "close_app", "target": "chrome"}
{"action": "set_brightness", "level": 70}
{"action": "screenshot"}
{"action": "type_text", "text": "hello world"}
{"action": "press_key", "key": "enter"}
{"action": "minimize_all"}

When the user asks a normal question, news, or anything else just reply normally in plain text.
Always be helpful, fast, and accurate.
Keep responses concise and clear."""
    }
]


def ask_ai(user_message):
    # Check if internet search needed
    if needs_youtube(user_message):
        videos = search_youtube(user_message)
        if videos and videos[0]["title"] != "Error":
            video_list = "\n".join([
                f'- {v["title"]} by {v["channel"]}: {v["url"]}'
                for v in videos[:3]
            ])
            return f"YOUTUBE_RESULTS:{video_list}"

    if needs_internet(user_message):
        results = search_web(user_message)
        if results:
            # Build context from search results
            context = ""
            for r in results[:3]:
                context += f"Title: {r['title']}\n"
                context += f"Summary: {r['summary']}\n"
                context += f"Link: {r['link']}\n\n"

            # Ask AI to summarize results
            search_prompt = f"""The user asked: {user_message}

Here are the latest search results:
{context}

Please provide a clear, helpful answer based on these results.
At the end list the sources with their links."""

            conversation_history.append({
                "role": "user",
                "content": search_prompt
            })
        else:
            conversation_history.append({
                "role": "user",
                "content": user_message
            })
    else:
        conversation_history.append({
            "role": "user",
            "content": user_message
        })

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=conversation_history,
        max_tokens=1024,
        temperature=0.7
    )

    reply = response.choices[0].message.content

    conversation_history.append({
        "role": "assistant",
        "content": reply
    })

    return reply