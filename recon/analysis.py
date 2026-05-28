import re
from .core import c, CYAN, GREEN, AMBER, RED, DIM, PURPLE, BOLD

def _gv(results, module, label):
    """安全获取字段值"""
    for f in results.get(module, {}).get("findings", []):
        if f.get("label") == label:
            return str(f.get("value", "")).strip()
    return ""

def compute_all_scores(results):
    """核心评分系统"""
    scores = {}

    # Security
    sec = 55
    dmarc = _gv(results, "email", "DMARC")
    if "p=reject" in dmarc: sec += 25
    elif "p=quarantine" in dmarc: sec += 15
    elif "未配置" in dmarc: sec -= 20

    issuer = _gv(results, "ssl", "颁发机构")
    if any(x in issuer.lower() for x in ["digicert","globalsign","sectigo"]): sec += 12
    elif "let's encrypt" in issuer.lower(): sec += 3

    if "缺失" in _gv(results, "headers", "安全响应头"):
        m = re.search(r'缺失 (\d+)', _gv(results, "headers", "安全响应头"))
        if m: sec -= int(m.group(1)) * 6

    scores["security"] = max(0, min(100, sec))
    scores["email"] = 75 if "p=reject" in dmarc else 45
    scores["infrastructure"] = 80 if "cloudflare" in _gv(results, "dns", "托管").lower() else 50
    scores["techdebt"] = 40 if "php/7" in _gv(results, "headers", "X-Powered-By").lower() else 70

    scores["overall"] = max(0, min(100, round(
        scores["security"]*0.35 + scores["email"]*0.20 + 
        scores["infrastructure"]*0.25 + scores["techdebt"]*0.20
    )))
    return scores


def run_analysis(domain, results, elapsed):
    scores = compute_all_scores(results)
    overall = scores["overall"]
    color = GREEN if overall >= 70 else AMBER if overall >= 50 else RED

    print(f"\n{c('═══════════════════════════════════════════════', DIM)}")
    print(f"  {c('RECON 深度分析 ·', BOLD)} {c(domain, CYAN)}")
    print(c('═══════════════════════════════════════════════', DIM))
    print(f"  总体健康度: {c(f'{overall}/100', color)}")

    # ==================== 商业洞察 ====================
    print(f"\n{c('◆ 关键商业洞察', PURPLE)}")

    hosting = _gv(results, "dns", "托管")
    if any(x in hosting.lower() for x in ["lolipop", "shared", "xserver"]):
        print(f"  • {c('低成本共享主机', AMBER)}：预算有限，典型中小企业或内容型站点")

    crm = _gv(results, "tech", "CRM/客服")
    if "未检测到" in crm:
        print(f"  • {c('无 CRM 系统', AMBER)}：销售靠人工管理，存在明显规模化瓶颈")

    dmarc = _gv(results, "email", "DMARC")
    if "未配置" in dmarc:
        print(f"  • {c('邮件安全薄弱', RED)}：易被用于钓鱼攻击，是极佳的销售切入点")

    issuer = _gv(results, "ssl", "颁发机构")
    if "let's encrypt" in issuer.lower():
        print(f"  • {c('使用免费证书', AMBER)}：InfoSec 预算有限，打企业客户时易被注意到")

    powered = _gv(results, "headers", "X-Powered-By")
    if "php/7" in powered.lower():
        print(f"  • {c('存在严重技术债', RED)}：PHP 7.x EOL，生产环境使用已停止更新的版本")

    print(f"\n{c('健康评分总览', BOLD)}")
    for key, label in [("overall", "总体"), ("security", "安全"), ("email", "邮件安全"),
                       ("infrastructure", "基础设施"), ("techdebt", "技术债")]:
        s = scores.get(key, 0)
        color = GREEN if s >= 70 else AMBER if s >= 50 else RED
        print(f"  {label.ljust(6)}: {c(f'{s}/100', color)}")

    print(c('═' * 56, DIM))
