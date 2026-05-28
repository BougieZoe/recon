import re, json
from .core import c, run, CYAN, AMBER, RED, DIM, GREEN

def _query_cdx(domain, limit=100):
    import urllib.request
    url = f"https://web.archive.org/cdx/search/cdx?url={domain}/*&output=json&limit={limit}&fl=timestamp,original,statuscode,mimetype"
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            return json.loads(r.read())
    except:
        return None

def _query_timemap(domain):
    import urllib.request
    url = f"https://web.archive.org/web/timemap/link/{domain}"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return r.read().decode()
    except:
        return None

def scan(domain, out):
    out.section("Wayback Machine 历史快照")
    import urllib.request

    data = _query_cdx(domain, limit=500)
    if data and len(data) > 1:
        total = len(data) - 1
        out.row("快照数量", c(str(total), CYAN), 'info')

        first_ts = data[1][0] if len(data) > 1 else ""
        if first_ts and len(first_ts) >= 8:
            year = first_ts[:4]
            out.row("最早快照", c(f"{year}年", GREEN), 'info')

        statuses = {}
        mimes = {}
        for row in data[1:]:
            if len(row) >= 4:
                s = row[2]
                statuses[s] = statuses.get(s, 0) + 1
                m = row[3]
                mimes[m] = mimes.get(m, 0) + 1

        status_str = ", ".join(f"{k}={v}" for k, v in sorted(statuses.items(), key=lambda x: -x[1])[:3])
        out.row("HTTP 状态码", status_str, 'info')

        if "text/html" in mimes:
            out.row("内容类型", c(f"HTML: {mimes.get('text/html', 0)} 页", DIM), 'info')

        unique_urls = len(set(row[1] for row in data[1:] if len(row) >= 2))
        out.row("唯一 URL", c(str(unique_urls), CYAN), 'info')

        if total > 1000:
            out.inference("快照>1000 → 该域长期活跃，历史可追溯。可查看旧版页面了解业务变迁。")
    else:
        out.row("Wayback", c("无数据或查询失败", AMBER), 'info')
