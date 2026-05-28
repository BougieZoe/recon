import re
import json
import socket
import ssl as tls
from .core import c, run, check_port, CONTEXT, CYAN, GREEN, AMBER, RED, DIM
from .rules import rule

CA_DB = [
    ("let's encrypt|letsencrypt", "Let's Encrypt (免费)", AMBER, "medium", "免费证书 = 无InfoSec预算。打Enterprise客户时IT部门会注意到。"),
    ("digicert|symantec|geo trust", "DigiCert (企业级)", GREEN, "low", None),
    ("globalsign", "GlobalSign (企业级)", GREEN, "low", None),
    ("sectigo|comodo|usertrust|addtrust", "Sectigo/Comodo", CYAN, "low", None),
    ("godaddy", "GoDaddy", CYAN, "info", None),
    ("zerossl", "ZeroSSL (免费)", AMBER, "medium", None),
    ("google trust|google", "Google Trust", GREEN, "low", None),
    ("amazon|awstrust", "Amazon Trust", GREEN, "low", None),
    ("cloudflare", "Cloudflare", GREEN, "low", None),
    ("microsoft", "Microsoft", GREEN, "low", None),
    ("buypass", "Buypass (免费)", AMBER, "medium", None),
    ("ssl.com", "SSL.com", CYAN, "low", None),
]

def _match_ca(issuer):
    for keyword, label, color, risk, inf in CA_DB:
        if any(k in issuer.lower() for k in keyword.split("|")):
            return label, color, risk, inf
    return issuer[:50], CYAN, "medium", None

def _query_crtsh(domain):
    for url in [f"https://crt.sh/?q=%25.{domain}&output=json", f"https://crt.sh/?q=.{domain}&output=json"]:
        try:
            import urllib.request
            with urllib.request.urlopen(url, timeout=10) as r:
                return json.loads(r.read())
        except:
            continue
    return None

def _get_cert_info(domain):
    ctx = tls.create_default_context()
    with socket.create_connection((domain, 443), timeout=8) as sock:
        with ctx.wrap_socket(sock, server_hostname=domain) as ssock:
            cert = ssock.getpeercert()
            issuer_parts = []
            for part in cert.get("issuer", []):
                for key, value in part:
                    issuer_parts.append(f"{key}={value}")
            return {
                "issuer": ", ".join(issuer_parts) or "Unknown",
                "not_after": cert.get("notAfter", ""),
                "tls_version": ssock.version() or "",
            }

def scan(domain, out):
    out.section("SSL / 证书")

    if CONTEXT.get("hosting") == "cloudflare":
        out.raw(c(f"\n  ⚠ 检测到 Cloudflare，SSL 证书信息可能来自 CDN，结果仅供参考。\n", AMBER))

    if not check_port(domain, 443):
        out.row("SSL 检查", c("443 端口未开放", AMBER), 'medium')
        return

    try:
        cert_info = _get_cert_info(domain)
    except Exception as e:
        out.row("SSL 握手", c(f"失败 ({e})", AMBER), 'medium')
        return

    issuer_str = cert_info.get("issuer") or "Unknown"

    label, ca_color, risk, inf = _match_ca(issuer_str)
    out.row("颁发机构", c(label, ca_color), risk)

    if "Let's Encrypt" in label or inf:
        out.inference(rule("ssl.letsencrypt", inf or "Let's Encrypt = 无InfoSec预算。打Enterprise客户时IT部门会注意到。"))

    if cert_info.get("not_after"):
        out.row("证书过期时间", cert_info["not_after"], 'info')

    data = _query_crtsh(domain)
    if data:
        names = list(set(d.get("name_value", "") for d in data if d.get("name_value")))
        real_names = [n for n in names if n != domain and not n.startswith("*")]
        out.row("子域名数量", f"{len(real_names)} 个", 'info')
        if real_names:
            out.inference(rule("ssl.subdomain_count", "每个子域名 = 一条业务线。无 staging/dev/api = 无工程团队。"))
    else:
        out.row("子域名", c("查询失败或超时", AMBER), 'medium')

    if cert_info.get("tls_version"):
        tls_label = cert_info["tls_version"].replace("v", " ")
        color = GREEN if cert_info["tls_version"] in ("TLSv1.3", "TLSv1.2") else RED
        out.row("协商 TLS 版本", c(tls_label, color), 'info')
