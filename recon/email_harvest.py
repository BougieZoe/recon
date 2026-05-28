import re
from .core import c, run, CYAN, AMBER, RED, DIM, GREEN

EMAIL_RE = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

def _scrape_page(domain):
    import urllib.request
    for scheme in ("https", "http"):
        try:
            with urllib.request.urlopen(f"{scheme}://{domain}", timeout=8) as r:
                return r.read().decode("utf-8", errors="ignore")
        except:
            continue
    return None

def _pgp_search(domain):
    import urllib.request
    try:
        url = f"https://keyserver.ubuntu.com/pks/lookup?search={domain}&op=index&fingerprint=on"
        with urllib.request.urlopen(url, timeout=8) as r:
            return r.read().decode("utf-8", errors="ignore")
    except:
        return None

def _google_dork(domain):
    import urllib.request
    try:
        url = f"https://www.google.com/search?q=site:{domain}+%40{domain}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            return r.read().decode("utf-8", errors="ignore")
    except:
        return None

def scan(domain, out):
    out.section("邮箱收集")
    all_emails = set()

    html = _scrape_page(domain)
    if html:
        found = re.findall(EMAIL_RE, html)
        for e in found:
            if e.lower().endswith(f"@{domain.lower()}"):
                all_emails.add(e.lower())
        if found:
            out.raw(f"\n  {c('✓ 页面扫描', GREEN)}")

    pgp = _pgp_search(domain)
    if pgp:
        found = re.findall(EMAIL_RE, pgp)
        for e in found:
            if domain in e:
                all_emails.add(e.lower())
        if found:
            out.raw(f"\n  {c('✓ PGP 密钥服务器', GREEN)}")

    if all_emails:
        sorted_emails = sorted(all_emails)[:20]
        out.row("发现邮箱", c(str(len(all_emails)), CYAN), 'info')
        out.raw(f"\n  {c('邮箱列表：', DIM)}")
        for e in sorted_emails:
            out.raw(f"\n    {c('✉', CYAN)} {e}")
        if len(all_emails) > 20:
            out.raw(f"\n    {c(f'... 还有 {len(all_emails) - 20} 个', DIM)}")
        out.inference("公开邮箱 = 钓鱼攻击面 + 社交工程入口。也是销售线索。")
    else:
        out.row("邮箱", c("未发现公开邮箱", AMBER), 'info')
