<p align="center">
  <img src="https://img.shields.io/badge/RECON-Passive%20Intel-%2322d3ee?style=flat-square" alt="RECON">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square" alt="Python">
  <img src="https://img.shields.io/badge/Platform-macOS%20%7C%20Linux%20%7C%20Windows%20%7C%20Termux-lightgrey?style=flat-square" alt="Platform">
  <img src="https://img.shields.io/badge/License-MIT-brightgreen?style=flat-square" alt="License">
</p>

<img width="1280" alt="Recon" src="https://github.com/user-attachments/assets/1f2b9f3f-62fe-4c69-8741-ad94c95af34a" />

<h1 align="center">🔍 RECON</h1>
<p align="center"><b>Passive Intelligence CLI</b> — Point at a domain or a person. Get an actionable intelligence brief in seconds.</p>

<p align="center">
  <code>recon example.com</code> · <code>recon -p</code> · <code>recon --web</code>
</p>

---

## ✨ Highlights

| What | How |
|------|-----|
| **Domain recon** | DNS, SSL, headers, email security, subdomains, tech stack, ASN/IP |
| **Person recon** | Public-data passive OSINT with AI-powered intent mapping |
| **Zero network probes** | No port scans, no active fingerprinting — fully passive |
| **No API keys required** | Everything comes from public sources (DNS, crt.sh, web scraping) |
| **Interactive TUI** | Real-time scan status, typewriter output, theme switching |
| **Export formats** | Markdown, JSON, PDF & clipboard-ready AI summaries |
| **Web UI** | Built-in Flask + Streamlit dashboards |
| **Cross-platform** | macOS, Linux, Windows (Docker/WSL), Termux (Android) |

---

## 🚀 Installation

### macOS / Linux / Termux (one-liner)

```bash
curl -fsSL https://raw.githubusercontent.com/BougieZoe/recon/main/install.sh | bash
```

This clones the repo, installs Python dependencies, and adds the `recon` alias to your shell.

### Manual setup

```bash
git clone https://github.com/BougieZoe/recon.git ~/.recon
cd ~/.recon
pip3 install -r requirements.txt
```

### Docker (zero dependencies — recommended for Windows)

```bash
docker build -t recon ~/.recon
docker run --rm recon example.com --report html
```

For **person mode** with Docker:

```bash
docker run -it --rm recon python3 recon.py --person
```

### Windows (via PowerShell)

```powershell
# Option A — Docker Desktop (recommended)
docker build -t recon %USERPROFILE%\.recon
docker run --rm recon example.com

# Option B — Python pip (requires Python 3.10+)
git clone https://github.com/BougieZoe/recon.git $env:USERPROFILE\.recon
cd $env:USERPROFILE\.recon
pip install -r requirements.txt
python recon.py example.com

# Option C — WSL (run the Linux install script)
wsl bash -c "$(curl -fsSL https://raw.githubusercontent.com/BougieZoe/recon/main/install.sh)"
```

---

## 🎯 Quick Start

```bash
# Domain intelligence
recon example.com

# Person intelligence (interactive TUI)
recon -p

# Launch the web dashboard
recon --web

# Offline demo mode for presentations
recon --demo --report html
```

---

## 📖 Usage

### Domain scanning

```bash
recon example.com                          # Single domain
recon example.com --analyze                # Deep analysis with scoring
recon example.com --parallel --analyze     # Parallel mode (3× faster)
recon example.com example.org --batch      # Batch comparison
```

### Output & reports

```bash
recon example.com --json --output scan.json          # JSON export
recon example.com --report md                        # Markdown report
recon example.com --report html && open recon_*.html  # HTML report
```

### History & comparison

```bash
recon --history     # View past scans
recon --diff 1 2    # Compare two scans
```

### Interactive terminal

```bash
recon -i            # Launch interactive TUI
```

### Demo mode (offline, no network)

```bash
recon --demo --report html
recon --demo --demo-profile legacy
```

---

## 👤 Person Mode

Person mode turns RECON into a passive OSINT tool for people. Enter a name, handle, or `name + company` — it scrapes public sources, feeds the data to an AI analyst, and produces a structured **intent map**.

```bash
recon --person
recon -p --theme cyan
recon -p --report md
```

### Input formats

| Format | Example |
|--------|---------|
| Full name | `Jane Smith` |
| Handle + website | `@janedoe + example.com` |
| Name + company | `Jane Smith + Acme Corp` |
| Website only | `https://example.com/about` |

### Data sources (100% passive)

| Source | Method |
|--------|--------|
| X / Twitter | Nitter mirrors (profile, bio, recent posts) |
| GitHub | Public API (bio, repos, organization) |
| News | DuckDuckGo HTML search |
| LinkedIn | Google cache of public profiles |
| Instagram | Public profile scrape + Google fallback |
| Website | Full page scrape when a URL is provided |

### AI intent map

All collected data is sent to **DeepSeek** (via OpenAI-compatible API) which returns:

| Field | Description |
|-------|-------------|
| `core_drive` | One-sentence summary of the person's fundamental motivation |
| `recurring_signals` | Topics, words, or emotions appearing 3+ times |
| `workarounds` | Clumsy detours that reveal real pain points |
| `direction` | Trajectory based on the last 6 months of signals |
| `contact_window` | Topic or framing most likely to get their attention |
| `confidence` | Confidence score (0–100) |
| `data_quality` | `high` · `medium` · `low` |

### Export options

After analysis, the interactive footer lets you export:

```
┌──────────────────────────────────────────────┐
│  [E] Export PDF  [M] Markdown  [J] JSON      │
│  [C] Copy for AI  [Q] Quit                   │
└──────────────────────────────────────────────┘
```

Press `1` · `2` · `3` to cycle themes (**cyan** · **green** · **pink**) mid-session.

### Themes

```bash
recon -p --theme cyan    # Cyberpunk cyan (default)
recon -p --theme green   # Matrix green
recon -p --theme pink    # Synthwave pink
```

### Person Web UI

```bash
recon -p --web
```

Starts a Flask server at `http://localhost:5001` with the same person analysis engine in your browser.

---

## 🧩 Modules

| Module | Function | Source |
|--------|----------|--------|
| `dns` | A/AAAA/MX/NS/TXT/SOA records + hosting detection | `dig` |
| `ssl` | Certificate authority, expiry, subdomains, TLS version | `openssl`, `crt.sh` |
| `headers` | Security headers, CDN detection, CORS, HTTP version | `curl` |
| `email` | SPF, DKIM, DMARC, MTA-STS | `dig` |
| `tech` | CMS, framework, CDN & third-party service fingerprinting | Response headers + page features |
| `basics` | WWW redirect, open port scan | `socket` |
| `subdomain` | Subdomain enumeration | `crt.sh` |
| `wayback` | Historical snapshots | Wayback Machine CDX |
| `email_harvest` | Email address extraction | Page scrape + PGP |
| `leak_search` | Credential leak search | HIBP + GitHub |
| `asn_ip` | IP geolocation, ASN lookup, VirusTotal check | Team Cymru + `dig` |

---

## 📊 Scoring

Five-axis weighted score (0–100):

```
Overall = Security × 35% + Infrastructure × 25% + Email × 20% + Tech Debt × 20%
```

| Axis | Factors |
|------|---------|
| **Security** | DMARC policy, SSL certificate quality, security headers, CDN |
| **Infrastructure** | Hosting provider, CDN, IPv6, DNS redundancy |
| **Email** | DMARC enforcement, DKIM, SPF `-all` |
| **Tech Debt** | PHP version, outdated components, free certificates |

---

## 🏗 Architecture

```
~/.recon/
├── recon.py                   ← Entry point (5 lines)
├── recon/                     ← Core package (28 files)
│   ├── core.py                ← ModuleOutput, ANSI colors, utilities
│   ├── cli.py                 ← CLI parser + interactive mode
│   ├── analysis.py            ← Scoring engine + business insights
│   ├── report.py              ← HTML / Markdown report generator
│   ├── history.py             ← SQLite scan history
│   ├── webapp.py              ← Streamlit web dashboard
│   ├── ssl.py / dns.py / ...  ← Scanner modules
│   ├── person.py              ← Person mode orchestrator
│   ├── person_sources.py      ← Public data scrapers
│   ├── person_ai.py           ← DeepSeek AI analysis
│   ├── person_render.py       ← Cyberpunk TUI renderer
│   ├── person_export.py       ← PDF / Markdown / JSON export
│   ├── person_client.py       ← Importable API client
│   ├── person_api_server.py   ← Flask API server
│   └── person_web.py          ← Web UI wrapper
├── modules/                   ← User plugins (drop `.py` files here)
├── Dockerfile
└── requirements.txt
```

---

## 🧪 Hackathon Notes

- **Demo mode**: `recon --demo --report html && open recon_*.html` — fully offline, zero chance of failure
- **Zero API keys**: All data comes from public sources — no signups, no rate limits
- **Web UI**: `recon --web` launches a Streamlit dashboard
- **Tech stack**: Pure Python 3 + stdlib — external deps are `openssl`, `dig`, `whois` (all bundled in Docker)

---

<p align="center">
  <i>Built for Hackathons · Passive Reconnaissance · AGI-powered Insights</i>
</p>
