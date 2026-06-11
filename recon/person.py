import asyncio
import threading
import json
import os
import subprocess
import sys
from datetime import datetime

from . import person_sources
from . import person_ai
from . import person_render
from . import person_export


def _build_target_info(parsed):
    info = {}
    t = parsed["type"]
    if t == "handle":
        info["handle"] = parsed["handle"]
    elif t == "handle_platform":
        info["handle"] = parsed["handle"]
        info["platform"] = parsed["platform"]
    elif t == "name":
        info["name"] = f"{parsed['first']} {parsed['last']}".strip()
    elif t == "name_company":
        info["name"] = f"{parsed['first']} {parsed['last']}".strip()
        info["company"] = parsed["company"]
    return info


def run_person_recon(input_str, export=None, theme=None):
    parsed = person_sources.parse_input(input_str)
    target_info = _build_target_info(parsed)

    t = person_render.theme_from_name(theme) if theme else person_render.CYAN_THEME

    person_render.render_header(theme=t)
    person_render.scan_animation(theme=t)

    sources = ["nitter", "github", "google_news", "linkedin", "instagram"]
    display = person_render.ReconDisplay(target_info, sources, theme=t)
    display.start()

    sources_data = {}
    intent_map = {}

    def status_cb(name, status):
        display.update_source(name, status)

    loop = asyncio.new_event_loop()

    def run_sources():
        asyncio.set_event_loop(loop)
        p, results = loop.run_until_complete(
            person_sources.run_all_sources(input_str, status_callback=status_cb)
        )
        loop.close()
        return p, results

    thread = threading.Thread(target=lambda: setattr(
        threading.current_thread(), "_result", run_sources()
    ))
    thread.start()
    thread.join()
    parsed, sources_data = thread._result

    display.stop()

    raw_parts = []
    for src_name, src_data in sources_data.items():
        if src_data.get("raw_text"):
            raw_parts.append(f"[{src_name}]\n{src_data['raw_text'][:2000]}")

    raw_text = "\n\n".join(raw_parts) if raw_parts else "No data collected from any source."

    try:
        intent_map = person_ai.analyze_person(raw_text)
    except Exception as e:
        intent_map = {
            "core_drive": "AI analysis failed",
            "recurring_signals": [],
            "workarounds": [],
            "direction": str(e),
            "contact_window": "",
            "confidence": 0,
            "data_quality": "low",
            "error": str(e),
        }

    person_render.render_intent_map_panel(intent_map, theme=t)

    pdf_theme = {"primary": t.primary, "warning": t.warning, "error": t.error}

    def run_export(action):
        nonlocal intent_map, sources_data, target_info, parsed
        name = target_info.get("name") or target_info.get("handle", "unknown")
        safe_name = name.replace(" ", "_").replace("/", "_")
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

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
                person_render.console.print("  copied to clipboard", style="green")
            except Exception:
                path = f"intel_{safe_name}_{ts}_ai.txt"
                with open(path, "w") as f:
                    f.write(md)
                person_render.console.print(f"  clipboard unavailable — saved to {path}", style="yellow")

    if export:
        run_export(export)
        return

    person_render.show_footer(theme=t)
    person_render.handle_footer(run_export, theme=t)
