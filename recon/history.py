import sqlite3, json, os
from datetime import datetime
from .core import c, CYAN, GREEN, AMBER, RED, DIM, BOLD
from .analysis import compute_all_scores

DB_PATH = os.path.expanduser("~/.recon/history.db")

def _get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            elapsed REAL,
            scores TEXT,
            results TEXT
        )
    """)
    conn.commit()
    return conn

def save_scan(domain, results, elapsed):
    conn = _get_db()
    scores = compute_all_scores(results)
    conn.execute(
        "INSERT INTO scans (domain, timestamp, elapsed, scores, results) VALUES (?, ?, ?, ?, ?)",
        (domain, datetime.now().isoformat(), round(elapsed, 2),
         json.dumps(scores, ensure_ascii=False),
         json.dumps(results, ensure_ascii=False))
    )
    conn.commit()
    scan_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    print(c(f"  ✓ 已保存 (ID: {scan_id})", GREEN))

def list_history():
    conn = _get_db()
    rows = conn.execute(
        "SELECT id, domain, timestamp, elapsed, scores FROM scans ORDER BY id DESC LIMIT 30"
    ).fetchall()
    conn.close()

    if not rows:
        print(c("  暂无历史记录", DIM))
        return

    print(f"\n{c('═'*56, BOLD)}")
    print(f"  {c('扫描历史', BOLD)}")
    print(c('═'*56, BOLD))
    print(f"  {c('ID'.ljust(4), DIM)} {c('域名'.ljust(22), DIM)} {'总体'.ljust(7)} {'时间'}")
    print(c('─'*56, DIM))

    for row in rows:
        scan_id, domain, ts, elapsed, scores_json = row
        try:
            scores = json.loads(scores_json) if scores_json else {}
            overall = scores.get("overall", 0)
        except: overall = 0
        color = GREEN if overall >= 70 else AMBER if overall >= 40 else RED
        time_str = ts[:19] if ts else "?"
        print(f"  {c(str(scan_id).ljust(4), CYAN)} {c(domain[:20].ljust(22), color)} "
              f"{c(str(overall).rjust(3)+'/100', color)} "
              f"{c(time_str, DIM)}")
    print(c('─'*56, DIM))
    print(c("  recon --diff <ID1> <ID2> 比较两次扫描\n", DIM))

def diff_scans(id1, id2):
    conn = _get_db()
    r1 = conn.execute("SELECT * FROM scans WHERE id=?", (id1,)).fetchone()
    r2 = conn.execute("SELECT * FROM scans WHERE id=?", (id2,)).fetchone()
    conn.close()

    if not r1 or not r2:
        print(c(f"  ✗ 未找到扫描 ID", RED))
        return

    def parse(r):
        return {"id": r[0], "domain": r[1], "ts": r[2][:19], "elapsed": r[3],
                "scores": json.loads(r[4]) if r[4] else {},
                "results": json.loads(r[5]) if r[5] else {}}

    a, b = parse(r1), parse(r2)

    print(f"\n{c('═'*56, BOLD)}")
    print(f"  {c('扫描对比', BOLD)}  {c(f'#{id1}', CYAN)} vs {c(f'#{id2}', CYAN)}")
    print(c('═'*56, BOLD))
    print(f"  {c('维度'.ljust(16), DIM)} {c(f'#{id1} ' + a['domain'], CYAN).ljust(18)} {c(f'#{id2} ' + b['domain'], CYAN)}")
    print(c('─'*56, DIM))

    for key, label in [("overall","总体"),("security","安全"),("infrastructure","基础设施"),
                       ("email","邮件"),("techdebt","技术债")]:
        s1 = a["scores"].get(key, 0); s2 = b["scores"].get(key, 0)
        diff = s2 - s1
        diff_str = f"+{diff}" if diff > 0 else str(diff)
        diff_color = GREEN if diff > 0 else RED if diff < 0 else DIM
        c1 = GREEN if s1 >= 70 else AMBER if s1 >= 40 else RED
        c2 = GREEN if s2 >= 70 else AMBER if s2 >= 40 else RED
        print(f"  {c(label.ljust(16), DIM)} {c(f'{s1}/100'.ljust(14), c1)} {c(f'{s2}/100'.ljust(14), c2)} {c(diff_str, diff_color)}")

    print(c('─'*56, DIM))
    print(f"  {c(a['domain'], DIM)} @ {a['ts']}  ({a['elapsed']}s)")
    print(f"  {c(b['domain'], DIM)} @ {b['ts']}  ({b['elapsed']}s)")
    print()
