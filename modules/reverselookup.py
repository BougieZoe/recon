import subprocess, re, urllib.request, json

METADATA = {"name": "reverselookup", "title": "关联资产反查"}

def _run(cmd, timeout=10):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout + r.stderr
    except:
        return ""

def scan(domain, out):
    ip = _run(["dig", "+short", domain, "A"]).strip().split('\n')[0] if _run(["dig", "+short", domain, "A"]) else ""
    if ip:
        out.section("IP 反查关联站点")
        out.row("目标 IP", ip, 'info')
        try:
            url = f"https://api.hackertarget.com/reverseiplookup/?q={ip}"
            req = urllib.request.urlopen(url, timeout=10)
            data = req.read().decode()
            sites = [s.strip() for s in data.split('\n') if s.strip() and not s.startswith('API')]
            if sites:
                out.row("同 IP 站点数", str(len(sites)), 'info')
                out.raw(f"\n  {out.col('关联资产地图：', out.c_dim)}")
                for s in sites[:10]:
                    out.raw(f"\n    {out.col('→', out.c_cyan)} {s}")
                if len(sites) > 10:
                    out.raw(f"\n    {out.col(f'... 还有 {len(sites)-10} 个', out.c_dim)}")
                inference_text = f"同IP {len(sites)} 个站点 = 共享主机确认。所有站点共享最低成本基础设施"
                if len(sites) > 20:
                    inference_text += "，内容农场/affiliate批量生产模式"
                out.inference(inference_text)
            else:
                out.row("同 IP 站点", out.col("无数据", out.c_dim), 'info')
        except Exception as e:
            out.row("IP 反查", out.col("API 查询失败", out.c_amber), 'medium')

    html = _run(["curl", "-sL", "--max-time", "8", f"https://{domain}"], timeout=10)
    if not html:
        html = _run(["curl", "-sL", "--max-time", "8", f"http://{domain}"], timeout=10)

    if html:
        out.section("GA ID 跨站关联")
        ga4 = list(set(re.findall(r'G-[A-Z0-9]{6,12}', html)))
        ua = list(set(re.findall(r'UA-\d{6,12}-\d{1,3}', html)))
        if ga4:
            out.row("GA4 ID", ga4[0], 'info')
            out.raw(f"\n  {out.col('★ 关键情报', out.c_amber)}")
            out.raw(f"\n  {out.col('用以下服务反查所有关联域名：', out.c_dim)}")
            out.raw(f"\n    {out.col(f'https://spyonweb.com/search?q={ga4[0]}', out.c_cyan)}")
            out.raw(f"\n    {out.col(f'https://builtwith.com/relationships/ga4/{ga4[0]}', out.c_cyan)}")
            out.inference(f"GA ID {ga4[0]} 可反查出该公司所有未公开的关联网站。同一个GA ID出现在多个域名 = 确认所有站属同一主体，这是确认关联资产最可靠的方式", out.c_amber)
        if ua:
            out.row("UA ID", ua[0], 'info')
