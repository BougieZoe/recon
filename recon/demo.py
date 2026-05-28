from copy import deepcopy

DEFAULT_PROFILE = "saas"

DEMO_SCANS = {
    "saas": {
        "domain": "brightlane.example",
        "elapsed": 2.4,
        "results": {
            "dns": {
                "findings": [
                    {"label": "IPv4", "value": "203.0.113.42", "risk": "info"},
                    {"label": "IPv6", "value": "未配置", "risk": "info"},
                    {"label": "托管", "value": "Cloudflare", "risk": "low"},
                    {"label": "邮件服务", "value": "Google Workspace", "risk": "low"},
                    {"label": "SPF", "value": "软失败 (~all) ⚠", "risk": "medium"},
                ],
                "inferences": [
                    "Cloudflare + Google Workspace 表明该团队有基础 SaaS 运维意识，但 SPF 仍处于宽松策略。"
                ],
            },
            "ssl": {
                "findings": [
                    {"label": "颁发机构", "value": "Let's Encrypt (免费)", "risk": "medium"},
                    {"label": "证书过期时间", "value": "Aug 18 12:00:00 2026 GMT", "risk": "info"},
                    {"label": "子域名数量", "value": "37 个", "risk": "info"},
                    {"label": "支持 TLS 版本", "value": "TLS 1.3, TLS 1.2", "risk": "info"},
                ],
                "inferences": [
                    "证书和子域名暴露出 api、staging、assets 等业务边界，适合做资产治理切入。"
                ],
            },
            "headers": {
                "findings": [
                    {"label": "CDN", "value": "Cloudflare ✓", "risk": "low"},
                    {"label": "Server", "value": "已隐藏 ✓", "risk": "low"},
                    {"label": "HTTP 版本", "value": "HTTP/2", "risk": "info"},
                    {"label": "安全响应头", "value": "缺失 2/7 项", "risk": "high"},
                    {"label": "CORS", "value": "未开放", "risk": "info"},
                    {"label": "响应时间", "value": "0.82s", "risk": "low"},
                ],
                "inferences": [
                    "缺失 CSP/HSTS 会影响企业客户安全评审，是低成本高优先级修复项。"
                ],
            },
            "email": {
                "findings": [
                    {"label": "DMARC", "value": "p=none ⚠ 仅监控", "risk": "medium"},
                    {"label": "DMARC 覆盖率", "value": "50% ⚠ 非全量", "risk": "medium"},
                    {"label": "DKIM", "value": "✓ google", "risk": "low"},
                    {"label": "MTA-STS", "value": "未配置 ⚠", "risk": "medium"},
                ],
                "inferences": [
                    "DMARC 只监控不拦截，说明邮件安全处在观察阶段，适合推进到 quarantine/reject。"
                ],
            },
            "tech": {
                "findings": [
                    {"label": "CMS", "value": "Next.js", "risk": "low"},
                    {"label": "前端框架", "value": "React, Tailwind CSS", "risk": "info"},
                    {"label": "GTM ID", "value": "GTM-DEMO42", "risk": "info"},
                    {"label": "第三方服务", "value": "HubSpot, Stripe, Sentry, reCAPTCHA", "risk": "info"},
                ],
                "inferences": [
                    "HubSpot + Stripe + Sentry 表明业务已在增长期，可从合规、支付安全和可观测性切入。"
                ],
            },
            "basics": {
                "findings": [
                    {"label": "www 解析", "value": "✓ www → 同IP (203.0.113.42)", "risk": "low"},
                    {"label": "开放端口", "value": "HTTP, HTTPS", "risk": "info"},
                ]
            },
            "asn_ip": {
                "findings": [
                    {"label": "IP 地址", "value": "203.0.113.42", "risk": "info"},
                    {"label": "IP 归属组织", "value": "Cloudflare, Inc.", "risk": "info"},
                    {"label": "国家", "value": "US", "risk": "info"},
                    {"label": "VT 检测", "value": "干净", "risk": "low"},
                ],
                "inferences": [
                    "CDN 归属清晰，源站未直接暴露，基础防护较成熟。"
                ],
            },
        },
    },
    "commerce": {
        "domain": "midorishop.example",
        "elapsed": 2.9,
        "results": {
            "dns": {
                "findings": [
                    {"label": "IPv4", "value": "198.51.100.24", "risk": "info"},
                    {"label": "托管", "value": "Xserver", "risk": "medium"},
                    {"label": "邮件服务", "value": "独立 MX", "risk": "medium"},
                    {"label": "SPF", "value": "配置但无-all", "risk": "medium"},
                ],
                "inferences": ["共享主机 + 独立邮件配置通常意味着电商团队运维预算有限。"],
            },
            "headers": {
                "findings": [
                    {"label": "CDN", "value": "无CDN ⚠ DDoS裸奔", "risk": "high"},
                    {"label": "Server", "value": "nginx 1.18", "risk": "medium"},
                    {"label": "安全响应头", "value": "缺失 5/7 项", "risk": "high"},
                    {"label": "响应时间", "value": "2.41s", "risk": "high"},
                ],
                "inferences": ["无 CDN 且响应慢，会同时影响安全、转化率和 SEO。"],
            },
            "email": {
                "findings": [
                    {"label": "DMARC", "value": "未配置 ✗", "risk": "high"},
                    {"label": "DKIM", "value": "未找到 ⚠", "risk": "medium"},
                    {"label": "MTA-STS", "value": "未配置 ⚠", "risk": "medium"},
                ],
                "inferences": ["无 DMARC 的电商域名很容易被仿冒发货/退款邮件。"],
            },
            "tech": {
                "findings": [
                    {"label": "CMS", "value": "WordPress + Elementor", "risk": "medium"},
                    {"label": "WP REST API", "value": "开放 ⚠", "risk": "high"},
                    {"label": "第三方服务", "value": "Stripe, Google Tag Manager, Facebook Pixel", "risk": "info"},
                ],
                "inferences": ["WordPress 插件面和支付链路并存，适合做插件治理和交易安全评估。"],
            },
        },
    },
    "legacy": {
        "domain": "oldportal.example",
        "elapsed": 3.1,
        "results": {
            "dns": {
                "findings": [
                    {"label": "IPv4", "value": "192.0.2.80", "risk": "info"},
                    {"label": "托管", "value": "Lolipop 共享主机", "risk": "high"},
                    {"label": "邮件服务", "value": "未配置 MX", "risk": "high"},
                    {"label": "SPF", "value": "未配置 ✗", "risk": "high"},
                ],
                "inferences": ["共享主机 + 邮件记录缺失，通常意味着长期无人维护。"],
            },
            "ssl": {
                "findings": [
                    {"label": "SSL 检查", "value": "443 端口未开放", "risk": "medium"},
                ]
            },
            "email": {
                "findings": [
                    {"label": "DMARC", "value": "未配置 ✗", "risk": "high"},
                    {"label": "DKIM", "value": "未找到 ⚠", "risk": "medium"},
                    {"label": "MTA-STS", "value": "未配置 ⚠", "risk": "medium"},
                ],
                "inferences": ["邮件认证记录缺失，外部人员可轻易仿冒该域名发信。"],
            },
            "headers": {
                "findings": [
                    {"label": "CDN", "value": "无CDN ⚠ DDoS裸奔", "risk": "high"},
                    {"label": "Server", "value": "Apache 2.4", "risk": "medium"},
                    {"label": "X-Powered-By", "value": "PHP/7.4 ⚠ EOL!", "risk": "high"},
                    {"label": "安全响应头", "value": "缺失 7/7 项", "risk": "high"},
                ],
                "inferences": ["PHP 7.x EOL + 安全响应头全缺失，是典型遗留门户风险组合。"],
            },
            "tech": {
                "findings": [
                    {"label": "CMS", "value": "WordPress", "risk": "medium"},
                    {"label": "CRM/客服", "value": "未检测到", "risk": "high"},
                ],
                "inferences": ["无 CRM/客服工具，销售或支持流程可能高度人工化。"],
            },
        },
    },
}


def list_profiles():
    return sorted(DEMO_SCANS)


def get_demo_scan(domain=None, profile=DEFAULT_PROFILE, modules=None):
    demo = deepcopy(DEMO_SCANS.get(profile) or DEMO_SCANS[DEFAULT_PROFILE])
    demo_domain = domain or demo["domain"]
    results = demo["results"]
    if modules:
        selected = [m for m in modules if m in results]
        results = {m: results[m] for m in selected}
    return demo_domain, results, demo["elapsed"]
