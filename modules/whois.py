import subprocess, re

METADATA = {"name": "whois", "title": "WHOIS / 域名信息"}

def _run(cmd, timeout=10):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout + r.stderr
    except:
        return ""

def scan(domain, out):
    out.section("WHOIS / 域名信息")

    raw = _run(["whois", domain])

    created = re.search(r'(?:Creation Date|Created on|registered on|Created Date)(?:\s*:\s*)(.+)', raw, re.IGNORECASE)
    created_val = created.group(1).strip() if created else "—"
    out.row("注册日期", created_val, 'info')

    expires = re.search(r'(?:Registry Expiry Date|Expir(?:ation|y) Date)(?:\s*:\s*)(.+)', raw, re.IGNORECASE)
    if expires:
        out.row("过期日期", expires.group(1).strip(), 'info')

    org = re.search(r'(?:Registrant Organization|org(?:anization)?|Organization)(?:\s*:\s*)(.+)', raw, re.IGNORECASE)
    if org:
        out.row("注册组织", org.group(1).strip(), 'info')

    registrar = re.search(r'(?:Registrar|Sponsoring Registrar)(?:\s*:\s*)(.+)', raw, re.IGNORECASE)
    if registrar:
        out.row("注册商", registrar.group(1).strip(), 'info')

    ns = re.findall(r'Name Server(?:\s*:\s*)(.+)', raw, re.IGNORECASE)
    if ns:
        out.row("Name Server", ", ".join(n.strip() for n in ns[:3]), 'info')

    admin_email = re.search(r'Admin Email(?:\s*:\s*)(.+)', raw, re.IGNORECASE)
    if admin_email:
        out.row("管理联系邮箱", admin_email.group(1).strip(), 'medium')

    out.raw(f"\n  {out.col('→ 域名注册日期可推断公司运营时间线。注册人信息可关联其他实体。', out.c_dim)}")
