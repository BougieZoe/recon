import re
from .core import c, run, check_tool, check_port, GREEN, AMBER, RED, DIM, CYAN, BOLD
from .rules import rule

CMS_PATTERNS = [
    (["/wp-content/plugins/elementor"], "WordPress + Elementor", "medium"),
    (["/wp-content/", "wp-json", "wordpress"], "WordPress", "medium"),
    (["drupal", "/sites/default/", "/core/"], "Drupal", "medium"),
    (["joomla", "/components/", "/modules/", "com_content"], "Joomla", "medium"),
    (["shopify", "/cdn/shop/", "shopify.com"], "Shopify", "low"),
    (["__NEXT_DATA__", "/_next/static/"], "Next.js", "low"),
    (["laravel", "csrf-token", "livewire"], "Laravel", "info"),
    (["/skin/frontend/", "Magento", "mage-"], "Magento", "info"),
    (["squarespace", "static.squarespace"], "Squarespace", "low"),
    (["wix", "wixstatic.com", "wix.com"], "Wix", "low"),
    (["webflow", "webflow"], "Webflow", "low"),
    (["ghost", "ghost"], "Ghost", "info"),
    (["strapi"], "Strapi (Headless CMS)", "info"),
]

FRAMEWORK_SIGS = [
    ("React", ["react", "reactjs", "__NEXT_DATA__"]),
    ("Vue.js", ["vue", "vuejs", "vuex"]),
    ("Angular", ["angular", "ng-version"]),
    ("jQuery", ["jquery"]),
    ("Alpine.js", ["alpinejs", "x-data"]),
    ("Svelte", ["svelte"]),
    ("Bootstrap", ["bootstrap"]),
    ("Tailwind CSS", ["tailwind"]),
]

THIRD_PARTY = [
    ("HubSpot", ["hubspot", "hs-analytics", "hs-script", "hubspotutk"]),
    ("Intercom", ["intercom", "intercom.io", "intercom-messenger"]),
    ("Hotjar", ["hotjar", "hj.js"]),
    ("Stripe", ["stripe.com", "pk_live", "pk_test", "stripe-"]),
    ("LINE", ["line.me", "liff.line", "line-liff"]),
    ("Google Tag Manager", ["googletagmanager", "gtm.js"]),
    ("Facebook Pixel", ["facebook.com/tr", "fbq(", "fbq"]),
    ("SendGrid", ["sendgrid", "sg.com"]),
    ("Mailchimp", ["mailchimp", "mc.us", "list-manage"]),
    ("Salesforce", ["salesforce", "sfdc"]),
    ("Zendesk", ["zendesk", "zdassets"]),
    ("New Relic", ["newrelic", "nr-data"]),
    ("Sentry", ["sentry", "sentry.io", "raven"]),
    ("Datadog", ["datadog", "dd-rum"]),
    ("Cloudflare", ["cloudflare", "cf-"]),
    ("Auth0", ["auth0"]),
    ("Firebase", ["firebase", "firestore"]),
    ("Amplitude", ["amplitude"]),
    ("Mixpanel", ["mixpanel"]),
    ("Cookiebot", ["cookiebot"]),
    ("OneTrust", ["onetrust"]),
    ("TinyMCE", ["tinymce"]),
    ("reCAPTCHA", ["recaptcha", "google.com/recaptcha"]),
]

def scan(domain, out):
    out.section("技术指纹 / GA ID 反查")
    if not check_tool("curl"): out.raw(c("  curl 未安装", RED)); return
    url = f"https://{domain}" if check_port(domain, 443) else f"http://{domain}"
    html = run(["curl", "-sL", "--max-time", "10", url], timeout=12)
    if not html:
        out.raw(c("  页面获取失败\n", RED)); return

    cms_found = False
    for sigs, label, risk in CMS_PATTERNS:
        if any(s in html.lower() for s in sigs):
            color = {"high": RED, "medium": AMBER, "info": CYAN, "low": GREEN}.get(risk, CYAN)
            out.row("CMS", c(label, color), risk)
            if label == "WordPress":
                wp_ver = re.search(r'WordPress[\s/]([\d.]+)', html)
                if wp_ver: out.row("WP 版本", wp_ver.group(1), 'medium')
                if "/wp-json/" in html: out.row("WP REST API", c("开放 ⚠", RED), 'high')
                wp_plugins = re.findall(r'/wp-content/plugins/([^/]+)/', html)
                if wp_plugins:
                    seen = set()
                    for p in wp_plugins:
                        if p not in seen:
                            out.raw(f"\n    {c('插件', DIM)} {p}")
                            seen.add(p)
            elif "WordPress + Elementor" in label:
                out.row("页面构建器", "Elementor", 'medium')
            cms_found = True
            break
    if not cms_found:
        out.row("CMS", c("未检测到已知CMS", DIM), 'info')
        if re.search(r'<meta\s+name="generator"', html, re.IGNORECASE):
            gen = re.search(r'content="([^"]+)"', html)
            if gen: out.row("生成器", gen.group(1)[:40], 'info')

    frameworks = []
    for name, sigs in FRAMEWORK_SIGS:
        if any(s in html.lower() for s in sigs):
            frameworks.append(name)
    if frameworks: out.row("前端框架", ", ".join(frameworks), 'info')

    ga4 = list(set(re.findall(r'G-[A-Z0-9]{6,12}', html)))
    ua = list(set(re.findall(r'UA-\d{6,12}-\d{1,3}', html)))
    gtm = list(set(re.findall(r'GTM-[A-Z0-9]+', html)))
    if ga4: out.row("GA4 ID", c(ga4[0], AMBER), 'info')
    if ua: out.row("UA ID", c(ua[0], AMBER), 'info')
    if gtm: out.row("GTM ID", c(gtm[0], AMBER), 'info')
    if ga4 or ua:
        out.raw(f"\n  {c('★ 反向查询', BOLD+AMBER)}")
        out.raw(f"\n  {c('curl', CYAN)} {c(f'https://spyonweb.com/search?q={ga4[0] if ga4 else ua[0]}', DIM)}")
        out.inference(rule("tech.ga_id", "GA ID 可在 spyonweb.com 反查出所有关联网站。同ID跨多域 = 同一主体。", id=ga4[0] if ga4 else ua[0]), AMBER)

    found_tools = []
    for tool, sigs in THIRD_PARTY:
        if any(s in html.lower() for s in sigs):
            found_tools.append(tool)
    if found_tools:
        tool_str = ", ".join(found_tools)
        out.row("第三方服务", tool_str, 'info')
    else:
        out.row("CRM/客服", c("未检测到", RED), 'high')
        out.inference(rule("tech.no_crm", "无CRM = 销售线索靠人肉管理，规模化天花板。"))
