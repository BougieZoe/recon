import re, json
from .core import c, run, CYAN, AMBER, RED, DIM, GREEN
from .config import get_api

def _check_haveibeenpwned(domain):
    import urllib.request
    try:
        url = f"https://haveibeenpwned.com/domain/{domain}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            return r.read().decode()
    except:
        return None

def _github_search(domain):
    token = get_api("github_token")
    if not token:
        return None
    import urllib.request
    try:
        url = f"https://api.github.com/search/code?q={domain}+extension:env+extension:config+extension:yml"
        req = urllib.request.Request(url, headers={"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except:
        return None

def _pastebin_search(domain):
    import urllib.request
    try:
        url = f"https://psbdmp.ws/api/v3/search?q={domain}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            return json.loads(r.read())
    except:
        return None

def scan(domain, out):
    out.section("泄露 / GitHub 搜索")

    # HIBP
    out.raw(f"\n  {c('Have I Been Pwned', CYAN)}")
    hibp = _check_haveibeenpwned(domain)
    if hibp:
        breaches = re.findall(r'<h3[^>]*>(.+?)</h3>', hibp)
        if breaches:
            breach_names = [b.strip()[:40] for b in breaches[:5]]
            out.row("已知泄露", c(", ".join(breach_names), RED), 'high')
            out.inference("域名出现在已知泄露中 = 员工/用户凭据可能已泄露。")
        else:
            out.row("已知泄露", c("未发现", GREEN), 'low')
    else:
        out.raw(f" {c('(跳过)', DIM)}")

    # GitHub
    out.raw(f"\n  {c('GitHub', CYAN)}")
    gh = _github_search(domain)
    if gh is None:
        out.raw(f" {c('(需 github_token)', AMBER)}")
    elif gh.get("total_count", 0) > 0:
        items = gh.get("items", [])
        out.row("GitHub 结果", c(str(gh["total_count"]), RED) + c(" 个文件", DIM), 'high')
        for item in items[:5]:
            repo = item.get("repository", {}).get("full_name", "?")
            path = item.get("path", "?")
            out.raw(f"\n    {c('→', RED)} {repo}/{path}")
        out.inference("GitHub 泄露 = 凭据/密钥/配置暴露。高优先级处置。")
    else:
        out.row("GitHub 泄露", c("未发现", GREEN), 'low')

    # Pastebin
    out.raw(f"\n  {c('Pastebin', CYAN)}")
    pb = _pastebin_search(domain)
    if pb:
        count = len(pb) if isinstance(pb, list) else 0
        if count > 0:
            out.row("Pastebin 结果", c(str(count), RED) + c(" 个记录", DIM), 'high')
        else:
            out.raw(f" {c('安全', GREEN)}")
    else:
        out.raw(f" {c('(跳过)', DIM)}")
