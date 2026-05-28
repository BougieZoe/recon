from .core import c, run, check_tool, check_port, GREEN, AMBER, RED, DIM

def _dig_a(name):
    raw = run(["dig", "+short", name, "A"])
    low = raw.lower().lstrip()
    if low.startswith(";;") or "permission denied" in low or "timed out" in low or "[error:" in low:
        return ""
    return raw

def scan(domain, out):
    out.section("基础检查")
    www_ip = _dig_a(f"www.{domain}") if check_tool("dig") else ""
    www_val = www_ip.strip().split('\n')[0] if www_ip.strip() else "未解析"
    root_ip = _dig_a(domain) if check_tool("dig") else ""
    root_val = root_ip.strip().split('\n')[0] if root_ip.strip() else "—"
    if www_val == root_val:
        out.row("www 解析", c(f"✓ www → 同IP ({www_val})", GREEN), 'low')
    elif www_val == "未解析":
        out.row("www 解析", c("⚠ www 未解析", AMBER), 'medium')
    else:
        out.row("www 解析", c(f"⚠ www→{www_val} ≠ root→{root_val}", AMBER), 'medium')

    ports = [(22, "SSH"), (80, "HTTP"), (443, "HTTPS"), (8080, "HTTP-Alt"), (8443, "HTTPS-Alt"), (21, "FTP")]
    open_ports = []
    for port, name in ports:
        if check_port(domain, port, timeout=2):
            open_ports.append(name)
    if open_ports:
        risk = "high" if "FTP" in open_ports or "SSH" in open_ports else "info"
        out.row("开放端口", c(", ".join(open_ports), RED if risk == "high" else GREEN), risk)
    else:
        out.row("开放端口", c("仅基础端口", DIM), 'info')
