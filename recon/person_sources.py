import asyncio
import random
import time
from datetime import datetime
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

NITTER_MIRRORS = [
    "https://nitter.net",
    "https://nitter.lqdev.org",
    "https://nitter.woodland.cafe",
    "https://nitter.cz",
]

PLATFORMS = {"x.com", "twitter.com", "github.com", "instagram.com", "linkedin.com"}


def parse_input(input_str):
    s = input_str.strip()
    if not s:
        return {"type": "raw", "text": ""}

    if " + " in s:
        parts = s.split(" + ", 1)
        name_part = parts[0].strip()
        company_part = parts[1].strip() if len(parts) > 1 else ""
        name_tokens = name_part.split() or [""]
        return {"type": "name_company", "first": name_tokens[0], "last": " ".join(name_tokens[1:]), "company": company_part}

    parts = s.split()
    if len(parts) == 1:
        return {"type": "handle", "handle": parts[0]}
    if len(parts) == 2:
        second = parts[1].lower().strip(",.!?")
        if second in PLATFORMS or "." in second:
            return {"type": "handle_platform", "handle": parts[0], "platform": second}
        return {"type": "name", "first": parts[0], "last": parts[1]}
    return {"type": "name", "first": parts[0], "last": " ".join(parts[1:])}


def guess_handles(first, last):
    base = first.lower() + last.lower()
    return [
        base,
        f"{first.lower()}.{last.lower()}",
        f"{first.lower()}_{last.lower()}",
        first.lower(),
        last.lower(),
    ]


def empty_result(source):
    return {"source": source, "raw_text": "", "posts": [], "bio": "", "timestamp": datetime.utcnow().isoformat()}


async def fetch_nitter(parsed, client, sem):
    async with sem:
        handles = []
        if parsed["type"] == "handle":
            handles = [parsed["handle"]]
        elif parsed["type"] == "handle_platform":
            handles = [parsed["handle"]]
        elif parsed["type"] in ("name", "name_company"):
            handles = guess_handles(parsed["first"], parsed["last"])

        result = empty_result("nitter")
        for handle in handles:
            for mirror in NITTER_MIRRORS:
                try:
                    await asyncio.sleep(random.uniform(0.5, 1.5))
                    url = f"{mirror}/{handle}"
                    resp = await client.get(url, timeout=15, follow_redirects=True)
                    if resp.status_code != 200:
                        continue
                    soup = BeautifulSoup(resp.text, "html.parser")
                    bio_el = soup.select_one(".profile-bio")
                    bio = bio_el.get_text(strip=True) if bio_el else ""
                    posts = []
                    for tweet in soup.select(".timeline-item"):
                        content_el = tweet.select_one(".tweet-content")
                        if content_el:
                            posts.append(content_el.get_text(strip=True))
                    raw = soup.get_text(separator=" ", strip=True)
                    return {
                        "source": f"nitter ({mirror})",
                        "raw_text": raw[:5000],
                        "posts": posts[:50],
                        "bio": bio,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                except Exception:
                    continue
        return result


async def fetch_github(parsed, client, sem):
    async with sem:
        result = empty_result("github")
        handles = []
        if parsed["type"] == "handle":
            handles = [parsed["handle"]]
        elif parsed["type"] == "handle_platform":
            handles = [parsed["handle"]]
        elif parsed["type"] in ("name", "name_company"):
            handles = guess_handles(parsed["first"], parsed["last"])

        for handle in handles:
            try:
                await asyncio.sleep(random.uniform(0.5, 1.5))
                resp = await client.get(f"https://api.github.com/users/{handle}", timeout=15)
                if resp.status_code != 200:
                    continue
                data = resp.json()
                return {
                    "source": "github",
                    "raw_text": str(data),
                    "posts": [],
                    "bio": data.get("bio") or data.get("company") or "",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            except Exception:
                continue
        return result


async def fetch_google_news(parsed, client, sem):
    async with sem:
        result = empty_result("google_news")
        query_parts = []
        if parsed["type"] in ("name", "name_company", "handle"):
            query_parts.append(parsed.get("first", "") + " " + parsed.get("last", ""))
        elif parsed["type"] == "handle_platform":
            query_parts.append(parsed["handle"])

        if parsed.get("company"):
            query_parts.append(parsed["company"])

        query = " ".join(p for p in query_parts if p)
        if not query:
            return result

        try:
            await asyncio.sleep(random.uniform(0.5, 1.5))
            url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"
            resp = await client.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code != 200:
                return result
            soup = BeautifulSoup(resp.text, "xml")
            posts = []
            for item in soup.select("item"):
                title = item.select_one("title")
                link = item.select_one("link")
                if title:
                    posts.append(f"{title.get_text(strip=True)} — {link.get_text(strip=True) if link else ''}")
            raw = soup.get_text(separator=" ", strip=True)
            return {
                "source": "google_news",
                "raw_text": raw[:5000],
                "posts": posts[:30],
                "bio": "",
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception:
            return result


async def fetch_linkedin_google(parsed, client, sem):
    async with sem:
        result = empty_result("linkedin")
        query_parts = ["site:linkedin.com/in"]
        if parsed["type"] in ("name", "name_company"):
            query_parts.append(f"{parsed['first']} {parsed['last']}")
        elif parsed["type"] == "handle":
            query_parts.append(parsed["handle"])
        elif parsed["type"] == "handle_platform":
            query_parts.append(parsed["handle"])

        if parsed.get("company"):
            query_parts.append(parsed["company"])

        query = " ".join(query_parts)
        try:
            await asyncio.sleep(random.uniform(0.5, 1.5))
            url = f"https://www.google.com/search?q={quote_plus(query)}&hl=en"
            resp = await client.get(url, timeout=15, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            })
            if resp.status_code != 200:
                return result
            soup = BeautifulSoup(resp.text, "html.parser")
            posts = []
            for link in soup.select("a[href*='linkedin.com']"):
                href = link.get("href", "")
                text = link.get_text(strip=True)
                if href and text:
                    posts.append(f"{text}: {href}")
            raw = soup.get_text(separator=" ", strip=True)
            return {
                "source": "linkedin (via google)",
                "raw_text": raw[:5000],
                "posts": posts[:20],
                "bio": "",
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception:
            return result


async def fetch_instagram(parsed, client, sem):
    async with sem:
        result = empty_result("instagram")
        handles = []
        if parsed["type"] == "handle":
            handles = [parsed["handle"]]
        elif parsed["type"] == "handle_platform":
            handles = [parsed["handle"]]
        elif parsed["type"] in ("name", "name_company"):
            handles = guess_handles(parsed["first"], parsed["last"])

        for handle in handles:
            try:
                await asyncio.sleep(random.uniform(0.5, 1.5))
                url = f"https://www.instagram.com/{handle}/"
                resp = await client.get(url, timeout=15, headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                })
                if resp.status_code != 200:
                    continue
                soup = BeautifulSoup(resp.text, "html.parser")
                raw = soup.get_text(separator=" ", strip=True)
                meta_bio = soup.select_one('meta[name="description"]')
                bio = meta_bio.get("content", "") if meta_bio else ""
                return {
                    "source": "instagram",
                    "raw_text": raw[:5000],
                    "posts": [],
                    "bio": bio,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            except Exception:
                continue

        if not result["raw_text"]:
            try:
                query = handles[0] if handles else ""
                if parsed.get("company"):
                    query += f" {parsed['company']}"
                await asyncio.sleep(random.uniform(0.5, 1.5))
                url = f"https://www.google.com/search?q={quote_plus('site:instagram.com ' + query)}"
                resp = await client.get(url, timeout=15, headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                })
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    raw = soup.get_text(separator=" ", strip=True)
                    result["raw_text"] = raw[:5000]
                    result["source"] = "instagram (fallback: google cache)"
            except Exception:
                pass

        return result


async def run_all_sources(input_str, status_callback=None):
    parsed = parse_input(input_str)
    async with httpx.AsyncClient(timeout=30) as client:
        sem = asyncio.Semaphore(3)

        async def run_one(name, coro):
            try:
                result = await coro
                if result.get("raw_text"):
                    if status_callback:
                        status_callback(name, "done")
                else:
                    if status_callback:
                        status_callback(name, "failed")
                return name, result
            except Exception as e:
                r = empty_result(name)
                r["raw_text"] = str(e)
                if status_callback:
                    status_callback(name, "failed")
                return name, r

        tasks = [
            run_one("nitter", fetch_nitter(parsed, client, sem)),
            run_one("github", fetch_github(parsed, client, sem)),
            run_one("google_news", fetch_google_news(parsed, client, sem)),
            run_one("linkedin", fetch_linkedin_google(parsed, client, sem)),
            run_one("instagram", fetch_instagram(parsed, client, sem)),
        ]

        final = {}
        for coro in asyncio.as_completed(tasks):
            name, result = await coro
            final[name] = result

        return parsed, final
