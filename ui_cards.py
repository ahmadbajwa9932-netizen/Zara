import customtkinter as ctk
import webbrowser
import threading
import requests
from PIL import Image, ImageTk
from io import BytesIO

# ============================================================
# NEWS CARD
# ============================================================

class NewsCard(ctk.CTkFrame):
    def __init__(self, parent, title, summary, link, index):
        super().__init__(
            parent,
            fg_color="#1a1a3e",
            corner_radius=12,
            border_width=1,
            border_color="#2a2a5e"
        )

        self.link = link
        self.grid_columnconfigure(0, weight=1)

        # Number badge
        badge = ctk.CTkLabel(
            self,
            text=f"  #{index}  ",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#00d4ff",
            text_color="#0f0f23",
            corner_radius=6
        )
        badge.grid(row=0, column=0, sticky="w", padx=12, pady=(10, 4))

        # Title
        title_label = ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#ffffff",
            wraplength=480,
            justify="left"
        )
        title_label.grid(row=1, column=0, sticky="w", padx=12, pady=(0, 4))

        # Summary
        summary_label = ctk.CTkLabel(
            self,
            text=summary[:200] + "..." if len(summary) > 200 else summary,
            font=ctk.CTkFont(size=12),
            text_color="#aaaacc",
            wraplength=480,
            justify="left"
        )
        summary_label.grid(row=2, column=0, sticky="w", padx=12, pady=(0, 8))

        # Read more button
        if link:
            read_btn = ctk.CTkButton(
                self,
                text="Read Full Article →",
                width=160,
                height=30,
                corner_radius=8,
                font=ctk.CTkFont(size=12),
                fg_color="#1e3a5f",
                hover_color="#2a4a7f",
                text_color="#00d4ff",
                command=lambda: webbrowser.open(link)
            )
            read_btn.grid(row=3, column=0, sticky="w", padx=12, pady=(0, 12))


# ============================================================
# YOUTUBE CARD
# ============================================================

class YouTubeCard(ctk.CTkFrame):
    def __init__(self, parent, title, channel, video_id, url, thumb_url):
        super().__init__(
            parent,
            fg_color="#1a1a3e",
            corner_radius=12,
            border_width=1,
            border_color="#ff0000"
        )

        self.url = url
        self.video_id = video_id
        self.grid_columnconfigure(1, weight=1)

        # YouTube badge
        yt_badge = ctk.CTkLabel(
            self,
            text="  ▶  YouTube  ",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#ff0000",
            text_color="#ffffff",
            corner_radius=6
        )
        yt_badge.grid(row=0, column=0, columnspan=2,
                      sticky="w", padx=12, pady=(10, 6))

        # Thumbnail
        self.thumb_label = ctk.CTkLabel(self, text="Loading...",
                                         width=160, height=90)
        self.thumb_label.grid(row=1, column=0, padx=12, pady=(0, 12))

        # Load thumbnail in background
        if thumb_url:
            threading.Thread(
                target=self.load_thumbnail,
                args=(thumb_url,),
                daemon=True
            ).start()

        # Right side info
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.grid(row=1, column=1, sticky="nsew", padx=(0, 12))
        info_frame.grid_columnconfigure(0, weight=1)

        # Video title
        title_label = ctk.CTkLabel(
            info_frame,
            text=title,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#ffffff",
            wraplength=300,
            justify="left"
        )
        title_label.grid(row=0, column=0, sticky="w", pady=(0, 4))

        # Channel name
        channel_label = ctk.CTkLabel(
            info_frame,
            text=f"📺  {channel}",
            font=ctk.CTkFont(size=11),
            text_color="#aaaacc",
            justify="left"
        )
        channel_label.grid(row=1, column=0, sticky="w", pady=(0, 8))

        # Buttons frame
        btn_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="w")

        # Watch in browser button
        watch_btn = ctk.CTkButton(
            btn_frame,
            text="▶  Watch in Browser",
            width=160,
            height=32,
            corner_radius=8,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#ff0000",
            hover_color="#cc0000",
            text_color="#ffffff",
            command=lambda: webbrowser.open(url)
        )
        watch_btn.grid(row=0, column=0, padx=(0, 8))

        # Copy link button
        copy_btn = ctk.CTkButton(
            btn_frame,
            text="🔗 Copy Link",
            width=100,
            height=32,
            corner_radius=8,
            font=ctk.CTkFont(size=12),
            fg_color="#1e1e3f",
            hover_color="#2d2d5f",
            text_color="#00d4ff",
            command=lambda: self.copy_link(url)
        )
        copy_btn.grid(row=0, column=1)

    def load_thumbnail(self, url):
        try:
            response = requests.get(url, timeout=5)
            img_data = Image.open(BytesIO(response.content))
            img_data = img_data.resize((160, 90), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img_data)
            self.thumb_label.configure(image=photo, text="")
            self.thumb_label.image = photo
        except:
            self.thumb_label.configure(text="No thumbnail")

    def copy_link(self, url):
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(url)
        root.update()
        root.destroy()


# ============================================================
# NEWS RESULTS FRAME
# ============================================================

class NewsResultsFrame(ctk.CTkFrame):
    def __init__(self, parent, results):
        super().__init__(parent, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkLabel(
            self,
            text="🌐  Latest News Results",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#00d4ff"
        )
        header.grid(row=0, column=0, sticky="w", pady=(0, 8))

        # News cards
        for i, result in enumerate(results):
            card = NewsCard(
                self,
                title=result.get("title", "No title"),
                summary=result.get("summary", "No summary"),
                link=result.get("link", ""),
                index=i + 1
            )
            card.grid(row=i + 1, column=0, sticky="ew",
                      pady=(0, 8))


# ============================================================
# YOUTUBE RESULTS FRAME
# ============================================================

class YouTubeResultsFrame(ctk.CTkFrame):
    def __init__(self, parent, videos):
        super().__init__(parent, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkLabel(
            self,
            text="🎬  YouTube Results",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#ff4444"
        )
        header.grid(row=0, column=0, sticky="w", pady=(0, 8))

        # YouTube cards
        for i, video in enumerate(videos):
            card = YouTubeCard(
                self,
                title=video.get("title", ""),
                channel=video.get("channel", ""),
                video_id=video.get("video_id", ""),
                url=video.get("url", ""),
                thumb_url=video.get("thumb", "")
            )
            card.grid(row=i + 1, column=0, sticky="ew", pady=(0, 8))