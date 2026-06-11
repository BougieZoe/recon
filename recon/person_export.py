import json
import os
from datetime import datetime


def generate_markdown(target_info, sources_data, intent_map):
    name = target_info.get("name") or target_info.get("handle", "unknown")
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    lines = []
    lines.append(f"# INTELLIGENCE BRIEF — {name} — {timestamp}")
    lines.append("")
    lines.append("## Target")
    for k, v in target_info.items():
        if v:
            lines.append(f"- **{k}**: {v}")
    lines.append("")

    lines.append("## Sources Collected")
    for src, data in sources_data.items():
        status = "✓" if data.get("raw_text") else "✗"
        lines.append(f"- {status} {src}")
    lines.append("")

    lines.append("## Intelligence Map")
    if "error" in intent_map:
        lines.append(f"\n> Error: {intent_map['error']}\n")
    else:
        lines.append(f"\n### Core Drive")
        lines.append(f"{intent_map.get('core_drive', 'N/A')}")
        lines.append("")
        lines.append(f"### Recurring Signals")
        for s in intent_map.get("recurring_signals", []):
            lines.append(f"- {s}")
        lines.append("")
        lines.append(f"### Workarounds")
        for w in intent_map.get("workarounds", []):
            lines.append(f"- {w}")
        lines.append("")
        lines.append(f"### Direction")
        lines.append(f"{intent_map.get('direction', 'N/A')}")
        lines.append("")
        lines.append(f"### Contact Window")
        lines.append(f"{intent_map.get('contact_window', 'N/A')}")
        lines.append("")
        lines.append(f"**Confidence**: {intent_map.get('confidence', 0)}/100  ")
        lines.append(f"**Data Quality**: {intent_map.get('data_quality', 'unknown').upper()}  ")

    return "\n".join(lines)


def generate_json(target_info, sources_data, intent_map):
    name = target_info.get("name") or target_info.get("handle", "unknown")
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    signals = intent_map.get("recurring_signals", [])
    workarounds = intent_map.get("workarounds", [])
    direction = intent_map.get("direction", "")
    contact = intent_map.get("contact_window", "")
    conf = intent_map.get("confidence", 0)
    dq = intent_map.get("data_quality", "unknown")

    context_parts = [
        f"Intelligence brief on {name}.",
        f"Core drive: {intent_map.get('core_drive', 'N/A')}.",
    ]
    if signals:
        context_parts.append(f"Key signals: {'; '.join(signals)}.")
    if workarounds:
        context_parts.append(f"Workarounds: {'; '.join(workarounds)}.")
    if direction:
        context_parts.append(f"Direction: {direction}.")
    if contact:
        context_parts.append(f"Contact window: {contact}.")
    context_parts.append(f"Confidence: {conf}/100. Data quality: {dq}.")

    doc = {
        "brief": f"INTELLIGENCE BRIEF — {name}",
        "timestamp": timestamp,
        "target": {k: v for k, v in target_info.items() if v},
        "sources": {},
        "analysis": intent_map,
        "ai_context": " ".join(context_parts),
    }

    for src_name, src_data in sources_data.items():
        doc["sources"][src_name] = {
            "status": "ok" if src_data.get("raw_text") else "failed",
            "bio": src_data.get("bio", ""),
            "post_count": len(src_data.get("posts", [])),
            "raw_sample": src_data.get("raw_text", "")[:500],
        }

    return json.dumps(doc, indent=2, ensure_ascii=False)


def _default_pdf_theme():
    return {
        "primary": "#22d3ee",
        "warning": "#f59e0b",
        "error": "#ef4444",
    }


def generate_pdf(target_info, sources_data, intent_map, theme=None):
    try:
        from weasyprint import HTML
    except ImportError:
        return None

    if theme is None:
        theme = _default_pdf_theme()

    name = target_info.get("name") or target_info.get("handle", "unknown")
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    signals = intent_map.get("recurring_signals", [])
    workarounds = intent_map.get("workarounds", [])
    direction = intent_map.get("direction", "")
    contact = intent_map.get("contact_window", "")
    conf = intent_map.get("confidence", 0)
    dq = intent_map.get("data_quality", "unknown")

    p = theme["primary"]
    w = theme["warning"]
    e = theme["error"]

    html_lines = [
        "<html><head><meta charset='utf-8'><style>",
        f"body {{ background: #000; color: {p}; font-family: monospace; padding: 40px; }}",
        f"h1 {{ color: {p}; border-bottom: 1px solid {p}; padding-bottom: 10px; }}",
        f"h2 {{ color: {w}; margin-top: 30px; }}",
        ".label { color: #6b7280; }",
        ".value { color: #ffffff; }",
        f".confidence {{ color: {p}; font-size: 1.2em; }}",
        f".quality {{ color: {w}; }}",
        "ul { color: #ffffff; }",
        "</style></head><body>",
        f"<h1>INTELLIGENCE BRIEF — {name}</h1>",
        f"<p><span class='label'>Generated:</span> <span class='value'>{timestamp}</span></p>",
        "<h2>Target</h2>",
    ]

    for k, v in target_info.items():
        if v:
            html_lines.append(f"<p><span class='label'>{k}:</span> <span class='value'>{v}</span></p>")

    html_lines.append("<h2>Sources Collected</h2><ul>")
    for src, data in sources_data.items():
        status = "✓" if data.get("raw_text") else "✗"
        color = p if data.get("raw_text") else e
        html_lines.append(f"<li style='color: {color}'>{status} {src}</li>")
    html_lines.append("</ul>")

    html_lines.append("<h2>Intelligence Map</h2>")
    if "error" not in intent_map:
        html_lines.append(f"<h3 style='color: {p}'>Core Drive</h3>")
        html_lines.append(f"<p class='value'>{intent_map.get('core_drive', 'N/A')}</p>")

        html_lines.append(f"<h3 style='color: {p}'>Recurring Signals</h3><ul>")
        for s in signals:
            html_lines.append(f"<li>{s}</li>")
        html_lines.append("</ul>")

        html_lines.append(f"<h3 style='color: {w}'>Workarounds</h3><ul>")
        for w_ in workarounds:
            html_lines.append(f"<li>{w_}</li>")
        html_lines.append("</ul>")

        html_lines.append(f"<h3 style='color: {p}'>Direction</h3>")
        html_lines.append(f"<p class='value'>{direction}</p>")

        html_lines.append(f"<h3 style='color: {w}'>Contact Window</h3>")
        html_lines.append(f"<p class='value'>{contact}</p>")

    html_lines.append(
        f"<p class='confidence'>Confidence: {conf}/100</p>"
    )
    html_lines.append(
        f"<p class='quality'>Data Quality: {dq.upper()}</p>"
    )

    html_lines.append("</body></html>")

    html_str = "\n".join(html_lines)
    pdf_path = f"intel_{name.replace(' ', '_')}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
    HTML(string=html_str).write_pdf(pdf_path)
    return pdf_path
