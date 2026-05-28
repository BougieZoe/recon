import os

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

KNOWLEDGE = {}

def load_knowledge():
    if not HAS_YAML: return
    path = os.path.expanduser("~/.recon/knowledge.yaml")
    if os.path.exists(path):
        with open(path) as f:
            KNOWLEDGE.update(yaml.safe_load(f) or {})

def detect_industry(results):
    def _gv(module, label):
        for f in results.get(module, {}).get("findings", []):
            if f.get("label") == label:
                return f.get("value", "").lower()
        return ""

    cms = _gv("tech", "CMS")
    hosting = _gv("dns", "托管")

    if "shopify" in cms: return "ecommerce"
    if "magento" in cms: return "ecommerce"
    if "woocommerce" in cms: return "ecommerce"
    if "wordpress" in cms and "elementor" in cms: return "ecommerce"
    if "wordpress" in cms: return "content_media"
    if "drupal" in cms: return "education_nonprofit"
    if "webflow" in cms or "squarespace" in cms: return "agency"
    if "wix" in cms: return "small_business"
    if "ghost" in cms: return "content_media"
    if "next.js" in cms or "laravel" in cms: return "saas"
    if "lolipop" in hosting: return "content_media"
    if "cloudflare" in hosting: return "saas"
    return "general"

def get_advice(industry):
    return KNOWLEDGE.get(industry, {}) if KNOWLEDGE else {}

def advice_section(domain, results):
    from .core import c, CYAN, AMBER, GREEN, RED, DIM, BOLD, PURPLE

    if not KNOWLEDGE:
        return

    ind = detect_industry(results)
    advice = get_advice(ind)
    if not advice:
        return

    print(f"\n{c('──────────────────────────────────────', DIM)}")
    print(f"  {c('◇', PURPLE)} {c('行业建议 · ' + advice.get('name', ind), BOLD)}")
    print(c('──────────────────────────────────────', DIM))

    if advice.get("description"):
        print(f"\n  {c(advice.get('description', ''), DIM)}")

    for item in advice.get("checklist", []):
        risk = item.get("risk", "medium")
        color = RED if risk == "high" else AMBER if risk == "medium" else GREEN
        print(f"  {c('•', color)} {c(item.get('text', ''), DIM)}")

    print()
