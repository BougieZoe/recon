import json
import os
import subprocess
import sys
import termios
import tty
from datetime import datetime

from . import person_render
from . import person_export
from .person_client import ReconClient


_client = None


def _get_client():
    global _client
    if _client is None:
        _client = ReconClient()
    return _client


def _parse_input(raw):
    raw = raw.strip()
    if not raw:
        return None, None
    if " + " in raw:
        parts = raw.split(" + ", 1)
        return parts[0].strip(), parts[1].strip()
    if raw.startswith("@"):
        return raw, None
    if "." in raw and "/" in raw:
        return None, raw
    return raw, None


def get_line(prompt_str):
    sys.stdout.write(prompt_str)
    sys.stdout.flush()

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    chars = []

    try:
        tty.setraw(fd)
        while True:
            b = os.read(fd, 1)
            if b in (b'\r', b'\n'):
                sys.stdout.write('\r\n')
                sys.stdout.flush()
                break
            elif b in (b'\x7f', b'\x08'):
                if chars:
                    chars.pop()
                    os.write(fd, b'\x08 \x08')
            elif b == b'\x03':
                raise KeyboardInterrupt
            elif b == b'\x15':
                n = len(chars)
                chars = []
                os.write(fd, b'\x08 \x08' * n)
            elif b[0] >= 32:
                chars.append(b.decode('utf-8', errors='replace'))
                os.write(fd, b)
    finally:
        termios.tcsetattr(fd, termios.TCSAFLUSH, old_settings)

    return ''.join(chars)


def run_person_recon(input_str=None, export=None, theme=None):
    t = person_render.theme_from_name(theme) if theme else person_render.GREEN_THEME
    theme_ref = [t]

    person_render.render_header(theme=t)

    if input_str is not None:
        _do_scan(input_str, t, export, theme_ref, website=None)
        return

    while True:
        console = person_render.console
        console.print()
        try:
            fd = sys.stdin.fileno()
            try:
                termios.tcsetattr(fd, termios.TCSAFLUSH, termios.tcgetattr(fd))
            except Exception:
                pass
            raw = get_line("  \u203a ")
        except (EOFError, KeyboardInterrupt):
            print()
            break

        target, website = _parse_input(raw)

        if not target and not website:
            console.print(f"[{t.error}]\u26a0 enter at least a name or website[/]")
            continue

        if target and website:
            display_info = f"{target} + {website}"
        elif target:
            display_info = target
        else:
            display_info = website

        _do_scan(target, t, export, theme_ref, website=website)
        t = theme_ref[0]

        if export:
            return

        person_render.render_search_footer(theme=t)
        choice = person_render.handle_search_footer(theme_ref=theme_ref)
        t = theme_ref[0]
        if choice == "q":
            break

    person_render.console.print(f"  exiting.", style=f"dim {t.primary}")


def _do_scan(target, t, export=None, theme_ref=None, website=None):
    sources = ["nitter", "github", "duckduckgo_news", "linkedin", "instagram"]
    if website:
        sources = sources + ["website"]
    target_info = {"target": target}
    if website:
        target_info["website"] = website

    person_render.scan_animation(theme=t)

    display = person_render.ReconDisplay(target_info, sources, theme=t)
    display.start()

    intent_map = {}
    data_warning_shown = False

    def on_source(name, status, text_length):
        display.update_source(name, status)

    def on_warning(msg):
        nonlocal data_warning_shown
        if not data_warning_shown:
            person_render.render_data_warning(theme=t)
            data_warning_shown = True

    def on_error(msg):
        pass

    intent_map = _get_client().analyze_sync(
        target=target, website=website or "",
        on_source=on_source, on_warning=on_warning, on_error=on_error,
    )

    if theme_ref:
        t = theme_ref[0]

    display.stop()

    if not intent_map:
        intent_map = {
            "core_drive": "No data collected",
            "recurring_signals": [],
            "workarounds": [],
            "direction": "",
            "contact_window": "",
            "confidence": 0,
            "data_quality": "low",
        }

    person_render.render_intent_map_panel(intent_map, theme=t)

    pdf_theme = {"primary": t.primary, "warning": t.warning, "error": t.error}

    def run_export(action):
        nonlocal intent_map, target_info
        name = target or "unknown"
        safe_name = name.replace(" ", "_").replace("/", "_")
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        sources_data = {}
        raw_sources = intent_map.get("_sources", {})
        for src_name, src_info in raw_sources.items():
            sources_data[src_name] = {
                "raw_text": "" if src_info.get("status") == "failed" else f"[data from {src_name}]",
                "bio": "",
                "posts": [],
            }

        if action == "m":
            md = person_export.generate_markdown(target_info, sources_data, intent_map)
            path = f"intel_{safe_name}_{ts}.md"
            with open(path, "w") as f:
                f.write(md)
            person_render.console.print(f"  exported markdown → {path}", style="green")

        elif action == "j":
            js = person_export.generate_json(target_info, sources_data, intent_map)
            path = f"intel_{safe_name}_{ts}.json"
            with open(path, "w") as f:
                f.write(js)
            person_render.console.print(f"  exported json → {path}", style="green")

        elif action == "e":
            path = person_export.generate_pdf(target_info, sources_data, intent_map, theme=pdf_theme)
            if path:
                person_render.console.print(f"  exported pdf → {path}", style="green")
            else:
                person_render.console.print("  PDF export unavailable (weasyprint not installed), falling back to markdown", style="yellow")
                md = person_export.generate_markdown(target_info, sources_data, intent_map)
                path = f"intel_{safe_name}_{ts}.md"
                with open(path, "w") as f:
                    f.write(md)
                person_render.console.print(f"  exported markdown → {path}", style="green")

        elif action == "c":
            md = person_export.generate_markdown(target_info, sources_data, intent_map)
            try:
                proc = subprocess.run(["pbcopy"], input=md, text=True, check=True)
                person_render.console.print(f"  copied to clipboard", style="green")
            except Exception:
                path = f"intel_{safe_name}_{ts}_ai.txt"
                with open(path, "w") as f:
                    f.write(md)
                person_render.console.print(f"  clipboard unavailable — saved to {path}", style="yellow")

    if export:
        run_export(export)
        return

    person_render.show_footer(theme=t)
    person_render.handle_footer(run_export, theme_ref=theme_ref)
