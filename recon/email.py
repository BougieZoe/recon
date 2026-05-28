import re
from .core import c, run, check_tool, GREEN, AMBER, RED, DIM
from .rules import rule

DKIM_SELECTORS = ["google", "default", "mail", "k1", "selector1", "selector2",
                  "s1", "s2", "dkim", "mx", "zoho", "proton", "sendgrid",
                  "mandrill", "postmark", "sparkpost", "ses", "mailgun",
                  "marketo", "hubspot", "salesforce"]

def _dig_txt(name):
    raw = run(["dig", "+short", name, "TXT"])
    low = raw.lower().lstrip()
    if low.startswith(";;") or "permission denied" in low or "timed out" in low or "[error:" in low:
        return None
    return raw

def scan(domain, out):
    out.section("邮件安全 (SPF/DKIM/DMARC/MTA-STS)")
    if not check_tool("dig"):
        out.raw(c("  dig 未安装\n", RED))
        return

    dmarc = _dig_txt(f"_dmarc.{domain}")
    if dmarc is None:
        out.row("DNS 查询", c("失败或被阻断", AMBER), 'medium')
        return

    has_dmarc = "v=DMARC1" in dmarc
    if has_dmarc:
        if "p=reject" in dmarc: out.row("DMARC", c("p=reject ✓ 最严格", GREEN), 'low')
        elif "p=quarantine" in dmarc: out.row("DMARC", c("p=quarantine 中等保护", AMBER), 'medium')
        elif "p=none" in dmarc: out.row("DMARC", c("p=none ⚠ 仅监控", AMBER), 'medium')
        pct = re.search(r'pct=(\d+)', dmarc)
        if pct and pct.group(1) != "100":
            out.row("DMARC 覆盖率", c(f"{pct.group(1)}% ⚠ 非全量", AMBER), 'medium')
        rua = re.search(r'rua=mailto:(\S+)', dmarc)
        if rua: out.row("DMARC 报告", c(rua.group(1), DIM), 'info')
    else:
        out.row("DMARC", c("未配置 ✗", RED), 'high')
        out.inference(rule("email.dmarc_missing", "无DMARC = 最佳销售切入点：「您的域名今天就可以被用来对您的客户发钓鱼邮件」。"), RED)

    dkim_found = False
    for sel in DKIM_SELECTORS:
        dkim = _dig_txt(f"{sel}._domainkey.{domain}")
        if dkim and "v=DKIM1" in dkim:
            out.row("DKIM", c(f"✓ {sel}", GREEN), 'low')
            dkim_found = True; break
    if not dkim_found:
        out.row("DKIM", c("未找到 ⚠", AMBER), 'medium')

    grade = "F" if not has_dmarc and not dkim_found else "C" if not has_dmarc or not dkim_found else "B"
    gc = RED if grade == 'F' else AMBER if grade in 'CD' else GREEN
    out.raw(f"\n  {c('邮件安全评级：', DIM)} {c(f'[ {grade} ]', gc)}")

    mta_sts = _dig_txt(f"_mta-sts.{domain}")
    if mta_sts and mta_sts.strip():
        out.row("MTA-STS", c("✓ 已配置", GREEN), 'low')
    else:
        out.row("MTA-STS", c("未配置 ⚠", AMBER), 'medium')

    bimi = _dig_txt(f"default._bimi.{domain}")
    if bimi and bimi.strip() and "v=BIMI1" in bimi:
        out.row("BIMI", c("✓ 已配置", GREEN), 'low')
