# RECON PERSON MODE — OpenCode Task Brief
# Project: ~/.recon | Author: Zoe | 2026-06-11

---

## Task

Add a `--person` mode to the existing recon CLI tool at `https://github.com/BougieZoe/recon`.

This mode takes a person's name/handle/company as input and outputs a structured intelligence map using public data sources + DeepSeek API analysis, rendered as a cyberpunk retro TUI animation.

---

## Step 1: Clone and inspect

```bash
git clone https://github.com/BougieZoe/recon ~/.recon
cd ~/.recon
cat requirements.txt
cat recon/cli.py
```

Tell me what you see before continuing.

---

## Step 2: Install new dependencies

Add these to `requirements.txt` then install:

```
httpx
beautifulsoup4
weasyprint
openai
```

```bash
pip3 install httpx beautifulsoup4 weasyprint openai --break-system-packages
```

---

## Step 3: Create `recon/person_sources.py`

Passive public data scraper. No API keys needed. Uses:

- `https://nitter.net/{username}` — X posts, bio, topics
- `https://api.github.com/users/{username}` — GitHub public API
- `https://news.google.com/rss/search?q={name}+{company}` — news mentions
- `https://www.google.com/search?q=site:linkedin.com+{name}+{company}` — LinkedIn via Google cache
- `https://www.instagram.com/{username}/` — public Instagram profile

Rules:
- Use `httpx` + `BeautifulSoup4`
- Each source in its own `try/except` — one failure must not crash the others
- Random delay 0.5–1.5s between requests
- Each source returns: `{"source": str, "raw_text": str, "posts": list, "bio": str, "timestamp": str}`
- Run all sources concurrently with `asyncio`

Input parsing — support 3 formats:
- `"firstname lastname"` → name only, guess handles
- `"handle x.com"` → explicit handle + platform
- `"firstname lastname company"` → name + company

---

## Step 4: Create `recon/person_ai.py`

Calls DeepSeek API via OpenAI-compatible client.

```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-1b8385467da1478bb26c26dab92f7e2f",
    base_url="https://api.deepseek.com"
)
```

System prompt:
```
You are a top-tier intelligence analyst.
You receive fragmented public data about a person.
Output a structured intent map as JSON only — no preamble, no markdown.

Required fields:
{
  "core_drive": "one sentence — what is this person fundamentally fighting for",
  "recurring_signals": ["topics/words/emotions appearing 3+ times"],
  "workarounds": ["clumsy detours they use — reveals real pain points"],
  "direction": "where are they heading based on last 6 months of signals",
  "contact_window": "what topic or framing would make them stop and look for 2 seconds",
  "confidence": 0-100,
  "data_quality": "high | medium | low"
}
```

Model: `deepseek-chat`

---

## Step 5: Create `recon/person_render.py`

Cyberpunk retro TUI renderer using `rich`.

Visual rules:
- Colors: cyan `#22d3ee` (primary), amber `#f59e0b` (warning), red `#ef4444` (error), black background
- Every line of output uses typewriter effect: print char by char with `time.sleep(0.02)`
- Between sections: ASCII scan line animation using `▓░` characters
- Blinking `>` cursor before each data line
- Use `rich.layout` for 3-panel layout:
  - Top left: target info (name / handle / company)
  - Top right: live source status (✓ / ✗ / scanning... per source)
  - Bottom: intent map results printed line by line

ASCII header (print at start of every run):
```
██████╗ ███████╗ ██████╗ ██████╗ ███╗   ██╗
██╔══██╗██╔════╝██╔════╝██╔═══██╗████╗  ██║
██████╔╝█████╗  ██║     ██║   ██║██╔██╗ ██║
██╔══██╗██╔══╝  ██║     ██║   ██║██║╚██╗██║
██║  ██║███████╗╚██████╗╚██████╔╝██║ ╚████║
╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝
[ PASSIVE INTELLIGENCE SYSTEM v2.0 — PERSON MODE ]
```

After results print, show this interactive footer:
```
┌──────────────────────────────────────────────┐
│  [E] Export PDF  [M] Export Markdown  [J] JSON│
│  [C] Copy for AI  [Q] Quit                    │
└──────────────────────────────────────────────┘
```

---

## Step 6: Create `recon/person_export.py`

Three export formats:

**PDF** (via weasyprint)
- Black background, cyan text, intelligence brief style
- Header: `INTELLIGENCE BRIEF — {name} — {timestamp}`
- Include confidence score and data quality indicator

**Markdown**
- Structured for feeding directly to other AIs (GPT, Gemini, Claude)
- Header: `# INTELLIGENCE BRIEF — {name} — {timestamp}`
- All analysis fields as clean sections

**JSON**
- Full raw data + analysis results
- Extra field: `"ai_context"` — a short natural language paragraph summarizing everything, so any AI can instantly understand the data without reading the whole JSON

---

## Step 7: Create `recon/person.py`

Main orchestrator:

```python
def run_person_recon(input_str: str, export: str = None):
    # 1. Parse input (name / handle / company)
    # 2. Launch all sources concurrently with asyncio
    #    Update TUI right panel in real time as each source completes
    # 3. Aggregate all raw_text, feed to DeepSeek via person_ai.py
    # 4. Render results with person_render.py (typewriter style)
    # 5. Show interactive footer, handle keypress for export
```

---

## Step 8: Patch `recon/cli.py`

Add to argparse:
```python
parser.add_argument('--person', '-p',
    metavar='TARGET',
    help='Person recon: "name", "handle platform", or "name company"')
```

Add to main:
```python
if args.person:
    from recon.person import run_person_recon
    run_person_recon(args.person, export=args.report)
```

---

## Step 9: Test

```bash
cd ~/.recon
python3 recon.py --person "name company" --theme pink
```

Expected: ASCII header (with theme colors in header line) → scan animation → sources updating live → intent map printing typewriter-style → interactive export footer

---

## Notes for OpenCode

- Instagram public API is unreliable — fallback to Google search cache if it fails
- nitter.net sometimes goes down — try 2-3 mirror instances before marking source as failed
- DeepSeek API call happens once at the end after ALL sources complete — not per source
- weasyprint can be tricky on some systems — if PDF export fails, markdown is the fallback
- This is passive recon only — no port scanning, no probes, public data only
