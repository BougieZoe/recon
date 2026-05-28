import re
from .core import c, run, check_tool, CONTEXT, CYAN, GREEN, AMBER, RED, DIM
from .rules import rule

HOSTING_DB = [
    ("lolipop", "Lolipop 共享主机", "high", "日本最便宜的共享主机。无专职运维"),
    ("cloudflare", "Cloudflare", "low", None),
    ("xserver", "Xserver", "medium", "日本主流VPS/共享主机"),
    ("sakura", "さくらインターネット", "medium", None),
    ("conoha", "ConoHa", "medium", "日本VPS"),
    ("starba|star-server", "スターサーバー", "medium", "低成本共享主机"),
    ("heteml", "Heteml", "medium", "日本VPS"),
    ("onamae|value-domain", "お名前.com", "medium", None),
    ("kagoya", "カゴヤ", "medium", "日本数据中心"),
    ("gmo", "GMO", "medium", None),
    ("aws|amazon", "AWS", "low", None),
    ("azure|microsoft", "Azure", "low", None),
    ("google", "Google Cloud", "low", None),
    ("digitalocean", "DigitalOcean", "low", None),
    ("linode|akamai", "Linode/Akamai", "low", None),
    ("vultr|constant", "Vultr", "low", None),
    ("namecheap|namcheap", "Namecheap", "medium", None),
]

def _match_hosting(ns_lower):
    for keyword, label, risk, desc in HOSTING_DB:
        if keyword in ns_lower or any(k in ns_lower for k in keyword.split("|")):
            return label, risk, desc
    return None, None, None

def _dig(domain, rrtype):
    raw = run(["dig", "+short", domain, rrtype])
    low = raw.lower().lstrip()
    if low.startswith(";;") or "permission denied" in low or "timed out" in low or "[error:" in low:
        return None
    return raw

def scan(domain, out):
    out.section("DNS 分析")
    tools_ok = check_tool("dig")
    if not tools_ok:
        out.row("DNS 查询", c("dig 未安装", RED), 'high')
        return

    mx = _dig(domain, "MX") if tools_ok else ""
    txt = _dig(domain, "TXT") if tools_ok else ""
    ns = _dig(domain, "NS") if tools_ok else ""
    ip = _dig(domain, "A") if tools_ok else ""
    ip6 = _dig(domain, "AAAA") if tools_ok else ""
    soa = _dig(domain, "SOA") if tools_ok else ""
    if all(v is None for v in (mx, txt, ns, ip, ip6, soa)):
        out.row("DNS 查询", c("失败或被阻断", AMBER), 'medium')
        return

    mx = mx or ""
    txt = txt or ""
    ns = ns or ""
    ip = ip or ""
    ip6 = ip6 or ""
    soa = soa or ""

    ip_val = ip.strip().split('\n')[0] if ip.strip() else '—'
    out.row("IPv4", c(ip_val, CYAN), 'info')
    if ip6.strip():
        out.row("IPv6", c(ip6.strip().split('\n')[0], CYAN), 'info')
    else:
        out.row("IPv6", c("未配置", DIM), 'info')

    if soa.strip():
        soa_parts = soa.strip().split()
        if len(soa_parts) >= 2:
            out.row("SOA 主 DNS", c(soa_parts[0], CYAN), 'info')
            admin = soa_parts[1].rstrip('.')
            admin = re.sub(r'\.', '@', admin, 1) if '@' not in admin else admin
            out.row("管理邮箱", c(admin, AMBER), 'info')

    ns_lower = ns.lower()
    label, risk, _ = _match_hosting(ns_lower)
    if label:
        color = RED if risk == "high" else AMBER if risk == "medium" else GREEN
        out.row("托管", c(label, color), risk)
        if "lolipop" in ns_lower:
            out.inference(rule("dns.lolipop", "共享主机 = 无工程预算。低成本内容型公司，无专职运维。"))
            CONTEXT["hosting"] = "lolipop"
        elif "cloudflare" in ns_lower:
            CONTEXT["hosting"] = "cloudflare"
        elif "xserver" in ns_lower:
            out.inference("Xserver = 日本主流VPS。可能有基础设施预算但有限")
            CONTEXT["hosting"] = "xserver"
    else:
        ns_val = ns.strip().split('\n')[0] if ns.strip() else '—'
        out.row("托管", ns_val, 'medium')

    mx_lower = mx.lower()
    if "google" in mx_lower:
        out.row("邮件服务", c("Google Workspace", GREEN), 'low')
    elif "outlook" in mx_lower or "microsoft" in mx_lower or "protection.outlook" in mx_lower:
        out.row("邮件服务", c("Microsoft 365", GREEN), 'low')
    elif "proton" in mx_lower:
        out.row("邮件服务", c("ProtonMail", GREEN), 'low')
    elif "zoho" in mx_lower:
        out.row("邮件服务", c("Zoho Mail", GREEN), 'low')
    elif not mx.strip():
        out.row("邮件服务", c("未配置 MX", RED), 'high')
    else:
        mx_host = mx.strip().split('\n')[0] if mx.strip() else '—'
        out.row("邮件服务", mx_host, 'medium')

    spf_match = re.search(r'v=spf1[^\n]+', txt, re.IGNORECASE)
    if spf_match:
        spf = spf_match.group(0).replace('" "', '').lower()
        if "~all" in spf:
            out.row("SPF", c("软失败 (~all) ⚠", AMBER), 'medium')
        elif "-all" in spf:
            out.row("SPF", c("硬失败 (-all) ✓", GREEN), 'low')
        elif "?all" in spf:
            out.row("SPF", c("中立 (?all) ⚠", AMBER), 'medium')
        else:
            out.row("SPF", c(f"配置但无-all", AMBER), 'medium')
    else:
        out.row("SPF", c("未配置 ✗", RED), 'high')
        out.inference(rule("dns.spf_missing", "无SPF = 你的域名今天就可以被用来发钓鱼邮件。"))
