import subprocess, re

METADATA = {"name": "redirect", "title": "HTTP 重定向链"}

def _run(cmd, timeout=10):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout + r.stderr
    except:
        return ""

def scan(domain, out):
    out.section("HTTP 重定向链分析")

    raw = _run(["curl", "-sIL", "--max-time", "10", f"http://{domain}"], timeout=12)

    if not raw:
        raw = _run(["curl", "-sIL", "--max-time", "10", f"https://{domain}"], timeout=12)

    status_codes = re.findall(r'^HTTP/(?:1\.[01]|2|3)\s+(\d{3})', raw, re.MULTILINE)
    locations = re.findall(r'^location:\s*(.+)$', raw, re.MULTILINE | re.IGNORECASE)

    redirect_count = len(locations)
    if redirect_count > 0:
        out.row("重定向次数", str(redirect_count), 'medium' if redirect_count > 1 else 'info')
        for i, loc in enumerate(locations[:3]):
            out.raw(f"\n  {out.col('  →', out.c_cyan)} {loc}")

    if "301" in status_codes or "302" in status_codes:
        out.row("HTTP→HTTPS", out.col("✓ 自动跳转", out.c_green), 'low')
    else:
        out.row("HTTP→HTTPS", out.col("⚠ 未跳转", out.c_red), 'high')

    if re.search(r'cf-ray|x-cache.*cloudflare', raw, re.IGNORECASE):
        out.row("CDN", out.col("Cloudflare ✓", out.c_green), 'low')
    elif re.search(r'x-amz-cf|cloudfront', raw, re.IGNORECASE):
        out.row("CDN", out.col("AWS CloudFront", out.c_green), 'low')
    elif re.search(r'fastly|x-served-by.*fastly', raw, re.IGNORECASE):
        out.row("CDN", out.col("Fastly", out.c_green), 'low')
    elif re.search(r'x-cache|akamai', raw, re.IGNORECASE):
        out.row("CDN", out.col("Akamai", out.c_green), 'low')
    else:
        out.row("CDN", out.col("无CDN ⚠ DDoS裸奔", out.c_red), 'high')
