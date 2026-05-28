import re
from .core import c, run, check_tool, check_port, GREEN, AMBER, RED, DIM, CYAN
from .rules import rule

SEC_HDRS = {
    "x-frame-options": "点击劫持防护",
    "content-security-policy": "CSP XSS防护",
    "strict-transport-security": "HSTS 强制HTTPS",
    "x-content-type-options": "MIME嗅探防护",
    "referrer-policy": "Referrer 隐私控制",
    "permissions-policy": "API权限控制",
    "x-xss-protection": "XSS过滤 (已弃用)",
}

def scan(domain, out):
    out.section("HTTP Headers 分析")
    if not check_tool("curl"):
        out.raw(c("  curl 未安装", RED)); return
    url = f"http://{domain}" if not check_port(domain, 443) else f"https://{domain}"
    raw = run(["curl", "-sI", "--max-time", "8", url], timeout=10)
    if not raw:
        out.raw(c("  HTTP 请求失败\n", RED)); return

    def h(name):
        m = re.search(rf'^{name}:\s*(.+)$', raw, re.MULTILINE | re.IGNORECASE)
        return m.group(1).strip() if m else None

    server = h("server"); powered = h("x-powered-by")
    cf_ray = h("cf-ray"); cf_cache = h("cf-cache-status")
    raw_lower = raw.lower()

    cdn = "无CDN ⚠"
    cdn_risk = 'high'
    if cf_ray:
        cdn = "Cloudflare"; cdn_risk = 'low'
        if cf_cache: cdn += f" ({cf_cache})"
    elif h("x-amz-cf-pop") or h("x-amz-cf-id"):
        cdn = "AWS CloudFront"; cdn_risk = 'low'
    elif h("x-served-by") and "fastly" in (h("x-served-by") or "").lower():
        cdn = "Fastly"; cdn_risk = 'low'
    elif h("x-cache") or "x-akamai-" in raw_lower:
        cdn = "Akamai"; cdn_risk = 'low'
    elif h("x-cdn") or "x-edge-" in raw_lower:
        cdn = "CDN (未识别)"; cdn_risk = 'low'
    cdn_text = f"{cdn} ✓" if cdn_risk == 'low' else "无CDN ⚠ DDoS裸奔"
    out.row("CDN", c(cdn_text, GREEN if cdn_risk == 'low' else RED), cdn_risk)

    if server:
        ver_exp = re.search(r'(Apache|nginx|IIS|Tomcat|Caddy|OpenResty|lighttpd|gunicorn|uwsgi)([\d.]*)', server, re.IGNORECASE)
        out.row("Server", c(f"{ver_exp.group(1)} {ver_exp.group(2)}" if ver_exp else f"{server} ⚠", AMBER), 'medium')
    else:
        out.row("Server", c("已隐藏 ✓", GREEN), 'low')

    if powered:
        eol = re.search(r'php/7\.[0-4]', powered.lower())
        out.row("X-Powered-By", c(f"{powered} {'⚠ EOL!' if eol else ''}", RED if eol else AMBER), 'high' if eol else 'medium')
        if eol:
            out.inference(rule("headers.php_eol", "PHP 7.x EOL = 已无安全更新。漏洞库有现成利用脚本。"), RED)

    http_v = re.search(r'^HTTP/(\S+)', raw)
    if http_v:
        v = http_v.group(1)
        out.row("HTTP 版本", c(f"HTTP/{v}", GREEN if v >= "2" else CYAN), 'info')

    missing = []
    for hdr, desc in SEC_HDRS.items():
        if not h(hdr): missing.append((hdr, desc))
    sec_score = len(SEC_HDRS) - len(missing)
    if missing:
        out.row("安全响应头", c(f"缺失 {len(missing)}/{len(SEC_HDRS)} 项", RED), 'high')
        for hdr, desc in missing:
            out.raw(f"\n    {c('✗', RED)} {hdr} ({desc})")
        csp = h("content-security-policy")
        hsts = h("strict-transport-security")
        if not csp and not hsts:
            out.inference(rule("headers.security_headers_missing", "无CSP+HSTS = 无XSS防护+无强制HTTPS。IT合规直接不通过。", count=len(missing)))
    else:
        out.row("安全响应头", c(f"全部 {sec_score}/{len(SEC_HDRS)} ✓", GREEN), 'low')

    origin = h("access-control-allow-origin")
    if origin and origin != "null":
        out.row("CORS", c(f"开放 ({origin}) ⚠", AMBER), 'medium')
    else:
        out.row("CORS", c("未开放", DIM), 'info')

    time_raw = run(["curl", "-w", "%{time_total}", "-sIo", "/dev/null", url, "--max-time", "8"], timeout=10)
    try:
        t = float(time_raw.strip())
        color = GREEN if t < 1 else AMBER if t < 2 else RED
        out.row("响应时间", c(f"{t:.2f}s", color) + (c(" ← SEO影响" if t > 1.5 else "", DIM)), 'low' if t < 1 else 'medium' if t < 2 else 'high')
    except: pass
