import re, json
from .core import c, run, CYAN, AMBER, RED, DIM, GREEN

def _get_ip(domain):
    raw = run(["dig", "+short", domain, "A"])
    low = raw.lower().lstrip()
    if low.startswith(";;") or "permission denied" in low or "timed out" in low or "[error:" in low:
        return None
    if raw.strip():
        return raw.strip().split('\n')[0]
    return None

def _whois_ip(ip):
    raw = run(["whois", ip])
    if not raw:
        return {}
    result = {}
    org = re.search(r'(?:org-name|OrgName|organisation|Organization|descr):\s*(.+)', raw, re.IGNORECASE)
    if org: result["org"] = org.group(1).strip()
    net = re.search(r'(?:inetnum|NetRange|CIDR):\s*(.+)', raw, re.IGNORECASE)
    if net: result["net"] = net.group(1).strip()
    country = re.search(r'(?:country|Country):\s*(.+)', raw, re.IGNORECASE)
    if country: result["country"] = country.group(1).strip()
    return result

def _cymru_lookup(query):
    import socket as sock
    try:
        s = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
        s.settimeout(5)
        s.connect(('whois.cymru.com', 43))
        s.sendall(f"{query}\n".encode())
        data = b''
        while True:
            try:
                chunk = s.recv(1024)
                if not chunk: break
                data += chunk
            except: break
        s.close()
        return data.decode()
    except:
        return None

def _cymru_asn(ip):
    raw = run(["dig", "+short", f"{ip}.origin.asn.cymru.com", "TXT"])
    if raw.strip():
        parts = raw.strip().strip('"').split("|")
        if len(parts) >= 3:
            as_name = parts[-1].strip()[:60] if len(parts) >= 7 else ""
            return {"asn": parts[0].strip(), "as_name": as_name}
    return None

def scan(domain, out):
    out.section("ASN / IP 归属")
    import shutil
    ip = _get_ip(domain)
    if not ip:
        out.row("IP", c("无法解析", RED), 'high')
        return
    out.row("IP 地址", c(ip, CYAN), 'info')

    if shutil.which("whois"):
        whois_data = _whois_ip(ip)
        if whois_data.get("org"):
            out.row("IP 归属组织", c(whois_data["org"][:50], AMBER), 'info')
        if whois_data.get("country"):
            out.row("国家", c(whois_data["country"], CYAN), 'info')
        if whois_data.get("net"):
            out.row("IP 段", c(whois_data["net"][:40], DIM), 'info')

    asn_data = _cymru_lookup(ip)
    if asn_data:
        lines = [l.strip() for l in asn_data.strip().split('\n') if l.strip()]
        if len(lines) >= 2:
            parts = [p.strip() for p in lines[1].split('|')]
            if len(parts) >= 1:
                asn_val = parts[0].replace('AS', '').strip()
                out.row("ASN", c(f"AS{asn_val}", CYAN), 'info')
                if len(parts) >= 7 and parts[-1]:
                    out.row("AS 名称", c(parts[-1][:50], AMBER), 'info')
                elif len(parts) >= 2:
                    out.row("AS 名称", c(parts[-1][:50], AMBER), 'info')

    # IP geolocation
    from .config import get_api
    vt_key = get_api("virustotal")
    if vt_key:
        try:
            import urllib.request
            url = f"https://www.virustotal.com/api/v3/ip_addresses/{ip}"
            req = urllib.request.Request(url, headers={"x-apikey": vt_key})
            with urllib.request.urlopen(req, timeout=8) as r:
                data = json.loads(r.read())
                attr = data.get("data", {}).get("attributes", {})
                if attr.get("as_owner"):
                    out.row("VT AS 持有者", c(attr["as_owner"][:50], AMBER), 'info')
                if attr.get("country"):
                    out.row("VT 国家", c(attr["country"], CYAN), 'info')
                if attr.get("last_analysis_stats"):
                    stats = attr["last_analysis_stats"]
                    malicious = stats.get("malicious", 0)
                    if malicious > 0:
                        out.row("VT 恶意标记", c(f"{malicious} 个引擎", RED), 'high')
                    else:
                        out.row("VT 检测", c("干净", GREEN), 'low')
        except:
            pass

    # Associated domains via reverse DNS
    ptr = run(["dig", "+short", "-x", ip])
    if ptr.strip():
        ptr_val = ptr.strip().split('\n')[0]
        out.row("反向 DNS", c(ptr_val[:50], DIM), 'info')

    out.inference(f"IP 归属可确认托管商/云服务商。ASN 信息可用于关联同一组织的其他资产。")
