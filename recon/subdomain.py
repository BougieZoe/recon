import re, json
from .core import c, run, CYAN, GREEN, AMBER, RED, DIM
from .config import get_api

def _query_crtsh(domain):
    for url in [
        f"https://crt.sh/?q=%25.{domain}&output=json",
        f"https://crt.sh/?q=.{domain}&output=json",
    ]:
        try:
            import urllib.request
            with urllib.request.urlopen(url, timeout=10) as r:
                return json.loads(r.read())
        except:
            continue
    return None

def _query_securitytrails(domain):
    key = get_api("securitytrails")
    if not key:
        return None
    try:
        import urllib.request
        req = urllib.request.Request(
            f"https://api.securitytrails.com/v1/domain/{domain}/subdomains",
            headers={"APIKEY": key, "Accept": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except:
        return None

def scan(domain, out):
    out.section("子域名枚举")
    all_subs = set()

    crtsh_data = _query_crtsh(domain)
    if crtsh_data:
        for d in crtsh_data:
            name = d.get("name_value", "")
            for n in name.splitlines():
                n = n.strip().lower()
                if n and n != domain and not n.startswith("*"):
                    all_subs.add(n)
        out.raw(f"\n  {c('crt.sh', CYAN)} ✓\n")

    st_data = _query_securitytrails(domain)
    if st_data and "subdomains" in st_data:
        for sub in st_data["subdomains"]:
            all_subs.add(f"{sub}.{domain}".lower())
        out.raw(f"  {c('SecurityTrails', CYAN)} ✓\n")

    if all_subs:
        sorted_subs = sorted(all_subs)
        out.row("发现子域名", c(str(len(sorted_subs)), CYAN), 'info')
        out.raw(f"\n  {c('子域名列表：', DIM)}")
        for s in sorted_subs[:15]:
            out.raw(f"\n    {c('→', CYAN)} {s}")
        if len(sorted_subs) > 15:
            out.raw(f"\n    {c(f'... 还有 {len(sorted_subs) - 15} 个', DIM)}")
        out.inference("子域名数量反映业务规模。查看 staging/dev/api 子域名可判断工程团队存在。")
    else:
        out.row("子域名", c("未发现 (或 API 不可用)", AMBER), 'info')
