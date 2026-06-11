import sys
import time
import random
import threading
from datetime import datetime
from dataclasses import dataclass

from rich.console import Console
from rich.columns import Columns
from rich.panel import Panel
from rich.text import Text
from rich.live import Live

console = Console()


@dataclass
class Theme:
    name: str
    primary: str
    warning: str
    error: str


CYAN_THEME = Theme("cyan", "#22d3ee", "#f59e0b", "#ef4444")
GREEN_THEME = Theme("green", "#00ff41", "#f59e0b", "#ef4444")
PINK_THEME = Theme("pink", "#ff6eb4", "#f59e0b", "#ef4444")

THEMES = {"cyan": CYAN_THEME, "green": GREEN_THEME, "pink": PINK_THEME}


def theme_from_name(name):
    return THEMES.get(name, CYAN_THEME)


HEADER_ART = r"""
██████╗ ███████╗ ██████╗ ██████╗ ███╗   ██╗
██╔══██╗██╔════╝██╔════╝██╔═══██╗████╗  ██║
██████╔╝█████╗  ██║     ██║   ██║██╔██╗ ██║
██╔══██╗██╔══╝  ██║     ██║   ██║██║╚██╗██║
██║  ██║███████╗╚██████╗╚██████╔╝██║ ╚████║
╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝
"""


def render_header(theme=None):
    t = theme or CYAN_THEME
    console.print()
    console.print()
    console.print()
    for line in HEADER_ART.strip("\n").split("\n"):
        console.print(Text(line, style=f"bold {t.primary}"))
    console.print(
        Text("[ PASSIVE INTELLIGENCE SYSTEM v2.0 — PERSON MODE ]", style=f"bold {t.primary}"),
        justify="center",
    )
    squares = Text("  ")
    squares.append("■ ", style=f"bold {CYAN_THEME.primary}")
    squares.append("■ ", style=f"bold {GREEN_THEME.primary}")
    squares.append("■", style=f"bold {PINK_THEME.primary}")
    console.print(squares, justify="center")
    console.print(
        Text("select theme with --theme [cyan | green | pink]", style=f"dim {t.primary}"),
        justify="center",
    )
    console.print()
    console.print()


def typewriter(text, delay=0.02, style=None):
    for char in text:
        console.print(char, style=style, end="")
        time.sleep(delay)
    console.print()


def scan_animation(theme=None):
    t = theme or CYAN_THEME
    console.print("  " + "─" * 60, style=f"dim {t.primary}")
    console.print()


class ReconDisplay:
    def __init__(self, target_info, sources, theme=None):
        self.target_info = target_info
        self.source_status = {s: "scanning" for s in sources}
        self.theme = theme or CYAN_THEME
        self.layout = self._build()
        self.live = None

    def _build(self):
        return self._render_full()

    def _render_full(self):
        t = self.theme
        return Panel(
            Text("\n".join(self._render_lines()), style=f"dim {self.theme.primary}"),
            border_style=self.theme.primary,
        )

    def _render_lines(self):
        lines = []
        lines.append("TARGET")
        for key in ("name", "handle", "company", "platform"):
            val = self.target_info.get(key) if key in self.target_info else ""
            lines.append(f"  {key}: {val if val else '___'}")
        lines.append("")
        lines.append("SOURCES")
        for src, status in self.source_status.items():
            icons = {"done": "✓", "failed": "✗", "scanning": "◉"}
            icon = icons.get(status, "?")
            lines.append(f"  {icon} {src}")
        return lines

    def update_source(self, source_name, status):
        self.source_status[source_name] = status
        if self.live:
            self.live.update(self._render_full())

    def start(self):
        self.live = Live(self.layout, refresh_per_second=10, screen=False)
        self.live.__enter__()
        return self

    def stop(self):
        if self.live:
            self.live.__exit__(None, None, None)
            self.live = None

def _build_intent_lines(intent_map):
    lines = []
    if "error" in intent_map:
        lines.append(f"  ERROR: {intent_map['error']}")
        return lines
    lines.append(f"  {intent_map.get('core_drive', '')}")
    signals = intent_map.get("recurring_signals", [])
    if signals:
        lines.append(f"  signals: {', '.join(signals)}")
    workarounds = intent_map.get("workarounds", [])
    if workarounds:
        lines.append(f"  workarounds: {', '.join(workarounds)}")
    lines.append(f"  direction: {intent_map.get('direction', '')}")
    lines.append(f"  contact: {intent_map.get('contact_window', '')}")
    conf = intent_map.get("confidence", 0)
    dq = intent_map.get("data_quality", "unknown")
    lines.append(f"  confidence: {conf}/100  |  data quality: {dq}")
    return lines


def render_intent_map_panel(intent_map, theme=None):
    t = theme or CYAN_THEME
    width = 72
    cw = width - 4
    lines = _build_intent_lines(intent_map)
    if not lines:
        return

    title = " INTENT MAP "
    lf = (width - len(title) - 2) // 2
    rf = width - len(title) - 2 - lf
    console.print(f"╭{'─' * lf}{title}{'─' * rf}╮", style=t.primary)

    for line in lines:
        console.print("│ ", style=t.primary, end="")
        for char in line.ljust(cw):
            console.print(char, style="white", end="")
            time.sleep(0.02)
        console.print(" │", style=t.primary)
        time.sleep(0.15)

    console.print(f"╰{'─' * (width - 2)}╯", style=t.primary)


def show_footer(theme=None):
    t = theme or CYAN_THEME
    console.print()
    console.print("┌──────────────────────────────────────────────┐", style=f"bold {t.primary}")
    console.print("│  [E] Export PDF  [M] Export Markdown  [J] JSON│", style=f"bold {t.primary}")
    console.print("│  [C] Copy for AI  [Q] Quit                    │", style=f"bold {t.primary}")
    console.print("└──────────────────────────────────────────────┘", style=f"bold {t.primary}")
    console.print()


def handle_footer(run_export_fn, theme=None):
    t = theme or CYAN_THEME
    while True:
        try:
            key = input("  select action: ").strip().lower()
            if key == "q":
                console.print("  exiting.", style=f"dim {t.primary}")
                return
            elif key in ("e", "m", "j", "c"):
                run_export_fn(key)
            else:
                console.print("  invalid key", style=f"dim {t.error}")
        except (EOFError, KeyboardInterrupt):
            console.print()
            return
