import os
os.environ["TCL_LIBRARY"] = r"C:\Users\Lenovo\AppData\Local\Programs\Python\Python313\tcl\tcl8.6"
os.environ["TK_LIBRARY"] = r"C:\Users\Lenovo\AppData\Local\Programs\Python\Python313\tcl\tk8.6"

import customtkinter as ctk
import threading
import datetime
import psutil
import platform
from ai_brain import ask_ai
from pc_control import execute_command
from ui_cards import NewsResultsFrame, YouTubeResultsFrame
from screen_reader import is_screen_command, handle_screen_command
from scheduler import is_schedule_command, handle_schedule_command
from shortcuts import is_shortcut_command, handle_shortcut_command

FONT_MAIN = "Rajdhani"      # futuristic, clean
FONT_MONO = "Share Tech Mono"  # sci-fi monospace

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ============================================================
# COLORS
# ============================================================
BG_MAIN    = "#020818"
BG_PANEL   = "#0a0a1a"
BG_CARD    = "#0d0d20"
NEON_BLUE  = "#00c8ff"
NEON_GREEN = "#00ff88"
NEON_PINK  = "#ff006e"
NEON_PURP  = "#7b2fff"
NEON_GOLD  = "#ffc200"   # add this — Jarvis uses gold/amber accents
TEXT_DIM   = "#4a4a6a"
TEXT_MID   = "#8888aa"
TEXT_LIGHT = "#ccccee"
TEXT_WHITE = "#ffffff"
BORDER     = "#1a1a3a"

# ============================================================
# MAIN APP
# ============================================================
class ZaraApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ZARA — Advanced AI System")
        self.geometry("1280x800")
        self.minsize(1000, 600)
        self.configure(fg_color=BG_MAIN)
        self.overrideredirect(False)  # keep for now, but consider True + custom titlebar later
        self.wm_attributes("-alpha", 0.97)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)
        self.grid_rowconfigure(1, weight=1)

        self.build_topbar()
        self.build_left_panel()
        self.build_center_panel()
        self.build_right_panel()

        self.update_stats()
        self.update_clock()
        self.load_headlines()
        self.welcome_message()

    def animate_radar(self):
        try:
            import math
            c = self.radar_canvas
            c.delete("all")
            w = c.winfo_width() or 1280
            h = 80

            # Dark grid
            for x in range(0, w, 60):
                c.create_line(x, 0, x, h, fill="#050d20", width=1)
            for y in range(0, h, 20):
                c.create_line(0, y, w, y, fill="#050d20", width=1)

            # Glowing horizon line
            c.create_line(0, h//2, w, h//2, fill="#0a2040", width=1)

            # Main waveform — smoother, more elegant
            points = []
            for x in range(0, w, 2):
                t = (x + self.radar_angle * 2) * 0.03
                y = h//2 + int(18 * math.sin(t) * math.exp(-0.0005 * ((x - w//2)**2) + 0.5))
                points.extend([x, y])
            if len(points) >= 4:
                c.create_line(points, fill="#003355", width=3, smooth=True)
                c.create_line(points, fill=NEON_BLUE, width=1, smooth=True)

            # Secondary waveform
            points2 = []
            for x in range(0, w, 2):
                t = (x + self.radar_angle * 1.5) * 0.05 + 1.2
                y = h//2 + int(9 * math.sin(t))
                points2.extend([x, y])
            if len(points2) >= 4:
                c.create_line(points2, fill=NEON_PURP, width=1, smooth=True)

            # Vertical scan bar with glow layers
            scan_x = (self.radar_angle * 3) % w
            for offset, alpha_color in [(12, "#010a18"), (6, "#021530"), (2, "#042a55"), (0, NEON_BLUE)]:
                c.create_rectangle(scan_x-offset, 0, scan_x+2, h, fill=alpha_color, outline="")

            # Corner HUD decorations
            c.create_text(16, 8, text="◈ NEURAL ACTIVITY", fill="#1a3a6a", font=("Segoe UI", 8), anchor="w")
            c.create_text(w-16, 8,
                text=f"SYN: {abs(int(math.sin(self.radar_angle * 0.05) * 999)):03d} Hz  |  LAT: {abs(int(math.cos(self.radar_angle*0.03)*50))} ms",
                fill="#1a3a6a", font=("Segoe UI", 8), anchor="e")

            self.radar_angle += 1
            self.after(20, self.animate_radar)   # faster = smoother
        except:
            pass

    # ============================================================
    # TOP BAR
    # ============================================================
    def build_topbar(self):
        self.topbar = ctk.CTkFrame(
            self, height=50, corner_radius=0,
            fg_color="#07071a",
            border_color=NEON_BLUE,
            border_width=1
        )
        self.topbar.grid(row=0, column=0, columnspan=3, sticky="ew")
        self.topbar.grid_columnconfigure(1, weight=1)

        # Logo
        ctk.CTkLabel(
            self.topbar,
            text="◤  Z · A · R · A    NEURAL AI  ◢",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=NEON_BLUE
        ).grid(row=0, column=0, padx=20, pady=10, sticky="w")

        # Clock
        self.clock_label = ctk.CTkLabel(
            self.topbar,
            text="",
            font=ctk.CTkFont(family="Rajdhani", size=13),
            text_color=NEON_GREEN
        )
        self.clock_label.grid(row=0, column=1, pady=10)

        # Status
        self.status_label = ctk.CTkLabel(
            self.topbar,
            text="● SYSTEM ONLINE",
            font=ctk.CTkFont(family="Rajdhani", size=12),
            text_color=NEON_GREEN
        )
        self.status_label.grid(row=0, column=2, padx=20, pady=10, sticky="e")

    # ============================================================
    # LEFT PANEL
    # ============================================================
    def build_left_panel(self):
        self.left = ctk.CTkFrame(
            self, width=240, corner_radius=0,
            fg_color=BG_PANEL,
            border_color=BORDER,
            border_width=1
        )
        self.left.grid(row=1, column=0, sticky="nsew")
        self.left.grid_propagate(False)
        self.left.grid_columnconfigure(0, weight=1)

        # System stats header
        self._section_label(self.left, "◈  SYSTEM MONITOR", 0)

        # CPU
        self.cpu_label = self._stat_label(self.left, "CPU", "0%", NEON_BLUE, 1)
        self.cpu_bar = ctk.CTkProgressBar(
            self.left, height=4,
            fg_color=BORDER,
            progress_color=NEON_BLUE
        )
        self.cpu_bar.grid(row=2, column=0, padx=15, pady=(0, 10), sticky="ew")
        self.cpu_bar.set(0)

        # RAM
        self.ram_label = self._stat_label(self.left, "RAM", "0%", NEON_PURP, 3)
        self.ram_bar = ctk.CTkProgressBar(
            self.left, height=4,
            fg_color=BORDER,
            progress_color=NEON_PURP
        )
        self.ram_bar.grid(row=4, column=0, padx=15, pady=(0, 10), sticky="ew")
        self.ram_bar.set(0)

        # Battery
        self.bat_label = self._stat_label(self.left, "BATTERY", "0%", NEON_GREEN, 5)
        self.bat_bar = ctk.CTkProgressBar(
            self.left, height=4,
            fg_color=BORDER,
            progress_color=NEON_GREEN
        )
        self.bat_bar.grid(row=6, column=0, padx=15, pady=(0, 10), sticky="ew")
        self.bat_bar.set(0)

        # Disk
        self.disk_label = self._stat_label(self.left, "DISK", "0%", NEON_PINK, 7)
        self.disk_bar = ctk.CTkProgressBar(
            self.left, height=4,
            fg_color=BORDER,
            progress_color=NEON_PINK
        )
        self.disk_bar.grid(row=8, column=0, padx=15, pady=(0, 15), sticky="ew")
        self.disk_bar.set(0)

        # Network
        self.net_label = self._stat_label(
            self.left, "NETWORK", "0 KB/s", NEON_GREEN, 9
        )
        # Divider
        ctk.CTkFrame(
            self.left, height=1,
            fg_color=BORDER
        ).grid(row=10, column=0, sticky="ew", padx=10, pady=5)

        # Quick commands header
        self._section_label(self.left, "◈  QUICK COMMANDS", 10)

        # Quick command buttons
        quick_cmds = [
            ("🌐  Open Chrome",    "open chrome"),
            ("📁  File Explorer",  "open explorer"),
            ("📸  Screenshot",     "take screenshot"),
            ("🔇  Mute Volume",    "mute"),
            ("📋  Show Tasks",     "show my tasks"),
            ("⚡  My Shortcuts",   "show shortcuts"),
        ]

        for i, (label, cmd) in enumerate(quick_cmds):
            btn = ctk.CTkButton(
                self.left,
                text=label,
                height=32,
                corner_radius=6,
                font=ctk.CTkFont(family="Rajdhani", size=11),
                fg_color="#050e25",
                hover_color="#0a1f45",
                text_color=NEON_BLUE,
                border_color=BORDER,
                border_width=1,
                anchor="w",
                command=lambda c=cmd: self.quick_send(c)
            )
            btn.grid(row=12+i, column=0, padx=12, pady=3, sticky="ew")

        # Divider
        ctk.CTkFrame(
            self.left, height=1,
            fg_color=BORDER
        ).grid(row=18, column=0, sticky="ew", padx=10, pady=5)

        # System info
        self._section_label(self.left, "◈  SYSTEM INFO", 19)
        os_info = f"{platform.system()} {platform.release()}"
        ctk.CTkLabel(
            self.left,
            text=f"OS: {os_info}",
            font=ctk.CTkFont(family="Rajdhani", size=10),
            text_color=TEXT_DIM
        ).grid(row=20, column=0, padx=15, pady=2, sticky="w")

        ctk.CTkLabel(
            self.left,
            text=f"PY: {platform.python_version()}",
            font=ctk.CTkFont(family="Rajdhani", size=10),
            text_color=TEXT_DIM
        ).grid(row=21, column=0, padx=15, pady=2, sticky="w")

        ctk.CTkLabel(
            self.left,
            text="AI: Llama 3.3 70B",
            font=ctk.CTkFont(family="Rajdhani", size=10),
            text_color=TEXT_DIM
        ).grid(row=22, column=0, padx=15, pady=2, sticky="w")

        ctk.CTkLabel(
            self.left,
            text="NET: Groq API",
            font=ctk.CTkFont(family="Rajdhani", size=10),
            text_color=TEXT_DIM
        ).grid(row=23, column=0, padx=15, pady=2, sticky="w")

    # ============================================================
    # CENTER PANEL
    # ============================================================
    def build_center_panel(self):
        self.center = ctk.CTkFrame(
            self, corner_radius=0,
            fg_color=BG_MAIN,
            border_color=BORDER,
            border_width=1
        )
        self.center.grid(row=1, column=1, sticky="nsew")
        self.center.grid_columnconfigure(0, weight=1)
        self.center.grid_rowconfigure(2, weight=1)

        # Animated radar canvas
        self.radar_canvas = ctk.CTkCanvas(
            self.center,
            height=80,
            bg=BG_MAIN,
            highlightthickness=0
        )
        self.radar_canvas.grid(row=0, column=0, sticky="ew")
        self.radar_angle = 0
        self.animate_radar()
        # Chat header
        chat_header = ctk.CTkFrame(
            self.center, height=35,
            fg_color=BG_PANEL,
            corner_radius=0,
            border_color=BORDER,
            border_width=1
        )
        chat_header.grid(row=1, column=0, sticky="ew")
        chat_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            chat_header,
            text="◈  NEURAL INTERFACE — CHAT",
            font=ctk.CTkFont(family="Rajdhani", size=11),
            text_color=TEXT_MID
        ).grid(row=0, column=0, padx=15, pady=8, sticky="w")

        # AI thinking indicator
        self.thinking_label = ctk.CTkLabel(
            chat_header,
            text="",
            font=ctk.CTkFont(family="Rajdhani", size=11),
            text_color=NEON_PINK
        )
        self.thinking_label.grid(row=0, column=1, padx=15, pady=8, sticky="e")

        # Chat area
        self.chat_frame = ctk.CTkScrollableFrame(
            self.center,
            corner_radius=0,
            fg_color=BG_MAIN,
            scrollbar_button_color=BORDER,
            scrollbar_button_hover_color=NEON_BLUE
        )
        self.chat_frame.grid(row=2, column=0, sticky="nsew")
        self.chat_frame.grid_columnconfigure(0, weight=1)

        # Input area
        input_frame = ctk.CTkFrame(
            self.center, height=70,
            fg_color=BG_PANEL,
            corner_radius=0,
            border_color=NEON_BLUE,
            border_width=1
        )
        input_frame.grid(row=3, column=0, sticky="ew")
        input_frame.grid_columnconfigure(0, weight=1)

        self.input_box = ctk.CTkEntry(
            input_frame,
            placeholder_text="  > AWAITING INPUT...",
            height=42,
            font=ctk.CTkFont(family="Rajdhani", size=13),
            corner_radius=8,
            border_color=NEON_BLUE,
            fg_color=BG_CARD,
            text_color=NEON_BLUE,
            placeholder_text_color=TEXT_DIM
        )
        self.input_box.grid(row=0, column=0, padx=(15,10), pady=14, sticky="ew")
        self.input_box.bind("<Return>", self.on_send)

        btn_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        btn_frame.grid(row=0, column=1, padx=(0,15), pady=14)

        self.send_btn = ctk.CTkButton(
            btn_frame,
            text="SEND",
            width=80,
            height=42,
            corner_radius=8,
            font=ctk.CTkFont(family="Rajdhani", size=12, weight="bold"),
            fg_color=NEON_BLUE,
            text_color=BG_MAIN,
            hover_color="#00aacc",
            command=self.on_send
        )
        self.send_btn.grid(row=0, column=0, padx=(0,8))

        self.voice_btn = ctk.CTkButton(
            btn_frame,
            text="🎤",
            width=42,
            height=42,
            corner_radius=8,
            font=ctk.CTkFont(size=18),
            fg_color=BG_CARD,
            hover_color="#1a1a3a",
            border_color=NEON_PURP,
            border_width=1,
            command=self.on_voice
        )
        self.voice_btn.grid(row=0, column=1, padx=(0,8))

        self.screen_btn = ctk.CTkButton(
            btn_frame,
            text="📸",
            width=42,
            height=42,
            corner_radius=8,
            font=ctk.CTkFont(size=18),
            fg_color=BG_CARD,
            hover_color="#1a1a3a",
            border_color=NEON_PINK,
            border_width=1,
            command=self.on_screenshot
        )
        self.screen_btn.grid(row=0, column=2)

    # ============================================================
    # RIGHT PANEL
    # ============================================================
    def build_right_panel(self):
        self.right = ctk.CTkFrame(
            self, width=260,
            corner_radius=0,
            fg_color=BG_PANEL,
            border_color=BORDER,
            border_width=1
        )
        self.right.grid(row=1, column=2, sticky="nsew")
        self.right.grid_propagate(False)
        self.right.grid_columnconfigure(0, weight=1)

        # Headlines header
        header_frame = ctk.CTkFrame(self.right, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=(12,6))
        header_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header_frame,
            text="◈  TODAY'S HEADLINES",
            font=ctk.CTkFont(family="Rajdhani", size=10, weight="bold"),
            text_color=NEON_BLUE
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            header_frame,
            text="↻",
            width=24,
            height=24,
            corner_radius=4,
            font=ctk.CTkFont(size=12),
            fg_color=BG_CARD,
            hover_color=BORDER,
            text_color=NEON_BLUE,
            command=self.load_headlines
        ).grid(row=0, column=1, sticky="e")

        # Headlines frame
        self.headlines_frame = ctk.CTkScrollableFrame(
            self.right,
            fg_color="transparent",
            height=320,
            scrollbar_button_color=BORDER
        )
        self.headlines_frame.grid(
            row=1, column=0,
            padx=8, pady=(0,10),
            sticky="nsew"
        )
        self.headlines_frame.grid_columnconfigure(0, weight=1)

        self.headlines_loading = ctk.CTkLabel(
            self.headlines_frame,
            text="Loading headlines...",
            font=ctk.CTkFont(family="Rajdhani", size=10),
            text_color=TEXT_DIM
        )
        self.headlines_loading.grid(row=0, column=0, pady=10)

        # Divider
        ctk.CTkFrame(
            self.right, height=1,
            fg_color=BORDER
        ).grid(row=2, column=0, sticky="ew", padx=10, pady=5)

        # Activity log header
        self._section_label(self.right, "◈  ACTIVITY LOG", 3)

        # Activity log
        self.activity_frame = ctk.CTkScrollableFrame(
            self.right,
            fg_color="transparent",
            height=220,
            scrollbar_button_color=BORDER
        )
        self.activity_frame.grid(
            row=4, column=0,
            padx=8, pady=(0,10),
            sticky="nsew"
        )
        self.activity_frame.grid_columnconfigure(0, weight=1)

        self.activity_count = 0

        # Divider
        ctk.CTkFrame(
            self.right, height=1,
            fg_color=BORDER
        ).grid(row=5, column=0, sticky="ew", padx=10, pady=5)

        # Zara status
        self._section_label(self.right, "◈  ZARA STATUS", 6)

        status_items = [
            ("VOICE ENGINE",   "READY",   NEON_GREEN),
            ("AI BRAIN",       "ONLINE",  NEON_GREEN),
            ("INTERNET",       "CONNECTED", NEON_GREEN),
            ("SCREEN READER",  "STANDBY", NEON_BLUE),
            ("SCHEDULER",      "ACTIVE",  NEON_GREEN),
            ("SHORTCUTS",      "LOADED",  NEON_GREEN),
        ]

        for i, (name, val, color) in enumerate(status_items):
            row_frame = ctk.CTkFrame(
                self.right,
                fg_color="transparent"
            )
            row_frame.grid(row=7+i, column=0, padx=12, pady=1, sticky="ew")
            row_frame.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                row_frame,
                text=name,
                font=ctk.CTkFont(family="Rajdhani", size=9),
                text_color=TEXT_DIM
            ).grid(row=0, column=0, sticky="w")

            ctk.CTkLabel(
                row_frame,
                text=f"● {val}",
                font=ctk.CTkFont(family="Rajdhani", size=9),
                text_color=color
            ).grid(row=0, column=1, sticky="e")

    # ============================================================
    # HELPERS
    # ============================================================
    def _section_label(self, parent, text, row):
        ctk.CTkLabel(
            parent,
            text=text,
            font=ctk.CTkFont(family="Rajdhani", size=10, weight="bold"),
            text_color=NEON_BLUE
        ).grid(row=row, column=0, padx=12, pady=(12,6), sticky="w")

    def _stat_label(self, parent, name, value, color, row):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=0, padx=15, pady=(4,2), sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame,
            text=name,
            font=ctk.CTkFont(family="Rajdhani", size=10),
            text_color=TEXT_DIM
        ).grid(row=0, column=0, sticky="w")

        lbl = ctk.CTkLabel(
            frame,
            text=value,
            font=ctk.CTkFont(family="Rajdhani", size=10, weight="bold"),
            text_color=color
        )
        lbl.grid(row=0, column=1, sticky="e")
        return lbl

    # ============================================================
    # UPDATE STATS
    # ============================================================
    def update_stats(self):
        try:
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent
            bat = psutil.sensors_battery()
            bat_pct = bat.percent if bat else 0

            self.cpu_label.configure(text=f"{cpu}%")
            self.ram_label.configure(text=f"{ram}%")
            self.disk_label.configure(text=f"{disk}%")
            self.bat_label.configure(text=f"{bat_pct}%")

            self.cpu_bar.set(cpu / 100)
            self.ram_bar.set(ram / 100)
            self.disk_bar.set(disk / 100)
            self.bat_bar.set(bat_pct / 100)
            # CPU temp if available
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    for name, entries in temps.items():
                        if entries:
                            temp = entries[0].current
                            self.cpu_label.configure(
                                text=f"{cpu}% | {temp:.0f}°C"
                            )
                            break
            except:
                pass
        except:
            # Network speed
            net1 = psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv
            time.sleep(0.1)
            net2 = psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv
            speed = (net2 - net1) / 1024
            self.net_label.configure(text=f"{speed:.0f} KB/s")
            pass
        self.after(3000, self.update_stats)

    # ============================================================
    # UPDATE CLOCK
    # ============================================================
    def update_clock(self):
        now = datetime.datetime.now()
        self.clock_label.configure(
            text=now.strftime("  %A  |  %d %B %Y  |  %I:%M:%S %p  ")
        )
        self.after(1000, self.update_clock)

    # ============================================================
    # LOAD HEADLINES
    # ============================================================
    def load_headlines(self):
        def fetch():
            try:
                from internet import search_web
                results = search_web("latest world news today", max_results=8)
                self.after(0, lambda: self.show_headlines(results))
            except Exception as e:
                self.after(0, lambda: self.headlines_loading.configure(
                    text=f"Could not load headlines"
                ))
        threading.Thread(target=fetch, daemon=True).start()
        self.after(300000, self.load_headlines)

    def show_headlines(self, results):
        for widget in self.headlines_frame.winfo_children():
            widget.destroy()

        for i, r in enumerate(results):
            card = ctk.CTkFrame(
                self.headlines_frame,
                fg_color=BG_CARD,
                corner_radius=6,
                border_color=BORDER,
                border_width=1
            )
            card.grid(row=i, column=0, sticky="ew", pady=3)
            card.grid_columnconfigure(0, weight=1)

            # Number
            ctk.CTkLabel(
                card,
                text=f"#{i+1}",
                font=ctk.CTkFont(family="Rajdhani", size=9),
                text_color=NEON_BLUE
            ).grid(row=0, column=0, padx=8, pady=(6,2), sticky="w")

            # Title
            title = r.get("title", "")[:60]
            ctk.CTkLabel(
                card,
                text=title,
                font=ctk.CTkFont(family="Rajdhani", size=9, weight="bold"),
                text_color=TEXT_LIGHT,
                wraplength=210,
                justify="left"
            ).grid(row=1, column=0, padx=8, pady=(0,2), sticky="w")

            # Summary
            summary = r.get("summary", "")[:80]
            ctk.CTkLabel(
                card,
                text=summary,
                font=ctk.CTkFont(family="Rajdhani", size=8),
                text_color=TEXT_DIM,
                wraplength=210,
                justify="left"
            ).grid(row=2, column=0, padx=8, pady=(0,6), sticky="w")

            # Click to read
            import webbrowser
            link = r.get("link", "")
            if link:
                card.bind("<Button-1>", lambda e, l=link: webbrowser.open(l))

    # ============================================================
    # ADD ACTIVITY LOG
    # ============================================================
    def log_activity(self, text, color=None):
        if color is None:
            color = TEXT_MID
        self.activity_count += 1
        time_str = datetime.datetime.now().strftime("%H:%M:%S")

        row_frame = ctk.CTkFrame(
            self.activity_frame,
            fg_color="transparent"
        )
        row_frame.grid(
            row=self.activity_count, column=0,
            sticky="ew", pady=1
        )

        ctk.CTkLabel(
            row_frame,
            text=f"{time_str}",
            font=ctk.CTkFont(family="Rajdhani", size=8),
            text_color=TEXT_DIM
        ).pack(side="left", padx=(4,6))

        ctk.CTkLabel(
            row_frame,
            text=text[:30],
            font=ctk.CTkFont(family="Rajdhani", size=8),
            text_color=color
        ).pack(side="left")

        self.after(100, lambda: self.activity_frame._parent_canvas.yview_moveto(1.0))

    # ============================================================
    # WELCOME MESSAGE
    # ============================================================
    def welcome_message(self):
        now = datetime.datetime.now()
        hour = now.hour
        if hour < 12:
            greet = "GOOD MORNING"
        elif hour < 17:
            greet = "GOOD AFTERNOON"
        else:
            greet = "GOOD EVENING"

        msg = (
            f"{greet}, ZOHAIB\n\n"
            f"ZARA SYSTEM INITIALIZED\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"CAPABILITIES ONLINE:\n"
            f"  [01]  PC CONTROL & AUTOMATION\n"
            f"  [02]  INTERNET SEARCH & NEWS\n"
            f"  [03]  YOUTUBE VIDEO SEARCH\n"
            f"  [04]  VOICE COMMAND INTERFACE\n"
            f"  [05]  FILE SYSTEM MANAGEMENT\n"
            f"  [06]  SCREEN READING & ANALYSIS\n"
            f"  [07]  SCHEDULED TASKS\n"
            f"  [08]  CUSTOM SHORTCUTS\n\n"
            f"AWAITING YOUR COMMAND..."
        )
        self.add_message(msg, sender="ai")
        self.log_activity("ZARA initialized", NEON_GREEN)

    # ============================================================
    # ADD MESSAGE
    # ============================================================
    def add_message(self, message, sender="user"):
        row = len(self.chat_frame.winfo_children())

        if sender == "user":
            bubble_color  = "#030f28"
            text_color    = NEON_BLUE
            align         = "e"
            label_text    = "[ ZOHAIB ]"
            label_color   = NEON_BLUE
            border_color  = NEON_BLUE
        else:
            bubble_color  = "#02081a"
            text_color    = TEXT_LIGHT
            align         = "w"
            label_text    = "[ ZARA ]"
            label_color   = NEON_GREEN
            border_color  = NEON_GREEN

        wrapper = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        wrapper.grid(row=row, column=0, sticky="ew", padx=10, pady=(4,0))
        wrapper.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            wrapper,
            text=label_text,
            font=ctk.CTkFont(family="Rajdhani", size=10, weight="bold"),
            text_color=label_color
        ).grid(row=0, column=0, sticky=align, padx=14)

        bubble = ctk.CTkFrame(
            wrapper,
            fg_color=bubble_color,
            corner_radius=12,
            border_color=border_color,
            border_width=1 if sender == "user" else 1,
        )
        bubble.grid(row=1, column=0, sticky=align, padx=10, pady=(2,2))

        ctk.CTkLabel(
            bubble,
            text=message,
            font=ctk.CTkFont(family="Rajdhani", size=12),
            text_color=text_color,
            wraplength=560,
            justify="left"
        ).pack(padx=14, pady=10)

        time_str = datetime.datetime.now().strftime("%H:%M:%S")
        ctk.CTkLabel(
            wrapper,
            text=time_str,
            font=ctk.CTkFont(family="Rajdhani", size=9),
            text_color=TEXT_DIM
        ).grid(row=2, column=0, sticky=align, padx=14)

        self.after(100, lambda: self.chat_frame._parent_canvas.yview_moveto(1.0))

    # ============================================================
    # ADD NEWS CARDS
    # ============================================================
    def add_news_cards(self, results, card_type="news"):
        row = len(self.chat_frame.winfo_children())
        wrapper = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        wrapper.grid(row=row, column=0, sticky="ew", padx=10, pady=(4,0))
        wrapper.grid_columnconfigure(0, weight=1)

        if card_type == "news":
            frame = NewsResultsFrame(wrapper, results)
        else:
            frame = YouTubeResultsFrame(wrapper, results)

        frame.grid(row=0, column=0, sticky="ew")
        self.after(100, lambda: self.chat_frame._parent_canvas.yview_moveto(1.0))

    # ============================================================
    # SHOW TYPING
    # ============================================================
    def show_typing(self):
        self.thinking_label.configure(text="◉ ZARA IS PROCESSING...")
        self._blink_thinking()

    def _blink_thinking(self):
        current = self.thinking_label.cget("text")
        if "PROCESSING" in current:
            self.thinking_label.configure(text_color=NEON_PINK)
            self._blink_job = self.after(500, self._blink_thinking)

    def hide_typing(self):
        self.thinking_label.configure(text="", text_color=NEON_PINK)

    # ============================================================
    # SET STATUS
    # ============================================================
    def set_status(self, text, color=NEON_GREEN):
        self.status_label.configure(
            text=f"● {text.upper()}",
            text_color=color
        )

    # ============================================================
    # QUICK SEND
    # ============================================================
    def quick_send(self, command):
        self.input_box.delete(0, "end")
        self.input_box.insert(0, command)
        self.on_send()

    # ============================================================
    # ON SEND
    # ============================================================
    def on_send(self, event=None):
        message = self.input_box.get().strip()
        if not message:
            return
        self.input_box.delete(0, "end")
        self.add_message(message, sender="user")
        self.log_activity(message[:30], NEON_BLUE)
        self.send_btn.configure(state="disabled")
        self.set_status("PROCESSING", NEON_PINK)
        self.show_typing()

        thread = threading.Thread(
            target=self.process_message, args=(message,)
        )
        thread.daemon = True
        thread.start()

    # ============================================================
    # PROCESS MESSAGE
    # ============================================================
    def process_message(self, message):
        try:
            from internet import needs_youtube, needs_internet, search_youtube, search_web
            from ai_brain import ask_ai

            # SHORTCUTS
            if is_shortcut_command(message):
                self.after(0, lambda: self.set_status("RUNNING SHORTCUT", NEON_PURP))
                def shortcut_callback(result_msg):
                    self.after(0, lambda: self.add_message(result_msg, sender="ai"))
                result = handle_shortcut_command(message, callback=shortcut_callback)
                self.after(0, self.hide_typing)
                self.after(0, lambda: self.add_message(result, sender="ai"))
                self.after(0, lambda: self.log_activity("Shortcut executed", NEON_PURP))
                self.after(0, lambda: self.set_status("ONLINE", NEON_GREEN))
                self.after(0, lambda: self.send_btn.configure(state="normal"))
                return

            # SCHEDULER
            if is_schedule_command(message):
                self.after(0, lambda: self.set_status("SCHEDULING", NEON_PURP))
                def schedule_callback(result_msg):
                    self.after(0, lambda: self.add_message(result_msg, sender="ai"))
                result = handle_schedule_command(message, callback=schedule_callback)
                self.after(0, self.hide_typing)
                self.after(0, lambda: self.add_message(result, sender="ai"))
                self.after(0, lambda: self.log_activity("Task scheduled", NEON_PURP))
                self.after(0, lambda: self.set_status("ONLINE", NEON_GREEN))
                self.after(0, lambda: self.send_btn.configure(state="normal"))
                return

            # SCREEN READING
            if is_screen_command(message):
                self.after(0, lambda: self.set_status("READING SCREEN", NEON_BLUE))
                result = handle_screen_command(message)
                self.after(0, self.hide_typing)
                if result:
                    self.after(0, lambda: self.add_message(result, sender="ai"))
                else:
                    response = ask_ai(message)
                    self.after(0, lambda: self.add_message(response, sender="ai"))
                self.after(0, lambda: self.log_activity("Screen read", NEON_BLUE))

            # YOUTUBE
            elif needs_youtube(message):
                self.after(0, lambda: self.set_status("SEARCHING YOUTUBE", NEON_PINK))
                videos = search_youtube(message)
                self.after(0, self.hide_typing)
                if videos and videos[0].get("title") != "Error":
                    self.after(0, lambda: self.add_message(
                        f"FOUND {len(videos)} VIDEOS:", sender="ai"
                    ))
                    self.after(100, lambda: self.add_news_cards(videos, "youtube"))
                else:
                    self.after(0, lambda: self.add_message(
                        "VIDEO SEARCH FAILED. TRY AGAIN.", sender="ai"
                    ))
                self.after(0, lambda: self.log_activity("YouTube searched", NEON_PINK))

            # INTERNET/NEWS
            elif needs_internet(message):
                self.after(0, lambda: self.set_status("SEARCHING WEB", NEON_BLUE))
                results = search_web(message, max_results=3)
                response = ask_ai(message)
                self.after(0, self.hide_typing)
                self.after(0, lambda: self.add_message(response, sender="ai"))
                if results:
                    self.after(200, lambda: self.add_news_cards(results, "news"))
                self.after(0, lambda: self.log_activity("Web searched", NEON_BLUE))

            # PC COMMAND OR NORMAL AI
            else:
                response = ask_ai(message)
                self.after(0, self.hide_typing)
                executed = execute_command(response)
                if executed:
                    self.after(0, lambda: self.add_message(
                        "COMMAND EXECUTED SUCCESSFULLY", sender="ai"
                    ))
                    self.after(0, lambda: self.log_activity("PC command done", NEON_GREEN))
                else:
                    self.after(0, lambda: self.add_message(response, sender="ai"))
                    self.after(0, lambda: self.log_activity("AI response", TEXT_MID))

            self.after(0, lambda: self.set_status("ONLINE", NEON_GREEN))

        except Exception as e:
            self.after(0, self.hide_typing)
            self.after(0, lambda: self.add_message(f"ERROR: {str(e)}", sender="ai"))
            self.after(0, lambda: self.log_activity("Error occurred", NEON_PINK))
            self.after(0, lambda: self.set_status("ERROR", NEON_PINK))

        finally:
            self.after(0, lambda: self.send_btn.configure(state="normal"))

    # ============================================================
    # VOICE
    # ============================================================
    def on_voice(self):
        self.voice_btn.configure(text="🔴")
        self.set_status("LISTENING", NEON_PINK)
        self.add_message("VOICE INTERFACE ACTIVE — SPEAK NOW", sender="ai")
        self.log_activity("Voice activated", NEON_PURP)

        def listen_thread():
            from voice import listen, speak
            text = listen()
            if text:
                self.after(0, lambda: self.add_message(text, sender="user"))
                self.after(0, lambda: self.set_status("PROCESSING", NEON_PINK))
                self.after(0, self.show_typing)
                from ai_brain import ask_ai
                response = ask_ai(text)
                self.after(0, self.hide_typing)
                executed = execute_command(response)
                if executed:
                    self.after(0, lambda: self.add_message(
                        "COMMAND EXECUTED", sender="ai"
                    ))
                    speak("Done")
                else:
                    self.after(0, lambda: self.add_message(response, sender="ai"))
                    speak(response)
            else:
                self.after(0, lambda: self.add_message(
                    "VOICE INPUT NOT DETECTED", sender="ai"
                ))
            self.after(0, lambda: self.voice_btn.configure(text="🎤"))
            self.after(0, lambda: self.set_status("ONLINE", NEON_GREEN))

        threading.Thread(target=listen_thread, daemon=True).start()

    # ============================================================
    # SCREENSHOT
    # ============================================================
    def on_screenshot(self):
        self.add_message("CAPTURING AND ANALYZING SCREEN...", sender="ai")
        self.set_status("ANALYZING", NEON_BLUE)
        self.log_activity("Screenshot taken", NEON_BLUE)

        def analyze():
            from screen_reader import ai_analyze_screen
            result = ai_analyze_screen("What do you see on my screen?")
            self.after(0, lambda: self.add_message(result, sender="ai"))
            self.after(0, lambda: self.set_status("ONLINE", NEON_GREEN))

        threading.Thread(target=analyze, daemon=True).start()

    def show_shortcuts(self):
        from shortcuts import list_shortcuts
        result = list_shortcuts()
        self.add_message(result, sender="ai")

    def show_tasks(self):
        from scheduler import get_pending_tasks
        tasks = get_pending_tasks()
        if not tasks:
            self.add_message("NO SCHEDULED TASKS.", sender="ai")
            return
        result = "SCHEDULED TASKS:\n\n"
        for t in tasks:
            result += f"#{t.task_id} — {t.description}\n"
            result += f"  TIME REMAINING: {t.time_remaining()}\n\n"
        self.add_message(result, sender="ai")

# ============================================================
# RUN
# ============================================================
if __name__ == "__main__":
    app = ZaraApp()
    app.mainloop()