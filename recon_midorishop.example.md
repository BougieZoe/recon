# RECON - midorishop.example

- Generated: 2026-05-28 23:44:08
- Elapsed: 2.9s
- Overall: 37/100
- Risk counts: high=5, medium=7, low=0, info=2

## Scores

- Security: 5/100
- Email: 45/100
- Infrastructure: 50/100
- Tech Debt: 70/100

## Priority Actions

- [高] email / DMARC: 未配置 ✗
  Evidence: DNS TXT records
  Recommendation: 将 DMARC 从 none 推进到 quarantine/reject，并确认 rua 报告链路可用。
- [高] headers / CDN: 无CDN ⚠ DDoS裸奔
  Evidence: HTTP response headers
  Recommendation: 接入 CDN/WAF，并确认源站不直接暴露在公网。
- [高] headers / 响应时间: 2.41s
  Evidence: HTTP response headers
  Recommendation: 优化首包和缓存策略；慢响应会同时影响 SEO、转化和扫描暴露面。
- [高] headers / 安全响应头: 缺失 5/7 项
  Evidence: HTTP response headers
  Recommendation: 补齐 CSP、HSTS、X-Content-Type-Options、Referrer-Policy 等安全响应头。
- [高] tech / WP REST API: 开放 ⚠
  Evidence: Homepage HTML fingerprint
  Recommendation: 限制 WordPress REST API 暴露面，审计插件和匿名接口。

## Findings

### email - DMARC
- Risk: 高
- Value: 未配置 ✗
- Evidence: DNS TXT records
- Recommendation: 将 DMARC 从 none 推进到 quarantine/reject，并确认 rua 报告链路可用。

### headers - CDN
- Risk: 高
- Value: 无CDN ⚠ DDoS裸奔
- Evidence: HTTP response headers
- Recommendation: 接入 CDN/WAF，并确认源站不直接暴露在公网。

### headers - 响应时间
- Risk: 高
- Value: 2.41s
- Evidence: HTTP response headers
- Recommendation: 优化首包和缓存策略；慢响应会同时影响 SEO、转化和扫描暴露面。

### headers - 安全响应头
- Risk: 高
- Value: 缺失 5/7 项
- Evidence: HTTP response headers
- Recommendation: 补齐 CSP、HSTS、X-Content-Type-Options、Referrer-Policy 等安全响应头。

### tech - WP REST API
- Risk: 高
- Value: 开放 ⚠
- Evidence: Homepage HTML fingerprint
- Recommendation: 限制 WordPress REST API 暴露面，审计插件和匿名接口。

### dns - SPF
- Risk: 中
- Value: 配置但无-all
- Evidence: DNS / dig
- Recommendation: 收敛 SPF include，最终使用 -all，避免域名被仿冒发信。

### dns - 托管
- Risk: 中
- Value: Xserver
- Evidence: DNS / dig
- Recommendation: 纳入近期加固计划，并在下一轮扫描中复核。

### dns - 邮件服务
- Risk: 中
- Value: 独立 MX
- Evidence: DNS / dig
- Recommendation: 纳入近期加固计划，并在下一轮扫描中复核。

### email - DKIM
- Risk: 中
- Value: 未找到 ⚠
- Evidence: DNS TXT records
- Recommendation: 为主要发信服务补齐 DKIM selector，并定期核对密钥轮换。

### email - MTA-STS
- Risk: 中
- Value: 未配置 ⚠
- Evidence: DNS TXT records
- Recommendation: 发布 MTA-STS policy，降低邮件传输链路被降级攻击的风险。

### headers - Server
- Risk: 中
- Value: nginx 1.18
- Evidence: HTTP response headers
- Recommendation: 纳入近期加固计划，并在下一轮扫描中复核。

### tech - CMS
- Risk: 中
- Value: WordPress + Elementor
- Evidence: Homepage HTML fingerprint
- Recommendation: 纳入近期加固计划，并在下一轮扫描中复核。

### dns - IPv4
- Risk: 信息
- Value: 198.51.100.24
- Evidence: DNS / dig
- Recommendation: 保留为资产画像证据，后续用于趋势对比。

### tech - 第三方服务
- Risk: 信息
- Value: Stripe, Google Tag Manager, Facebook Pixel
- Evidence: Homepage HTML fingerprint
- Recommendation: 保留为资产画像证据，后续用于趋势对比。

## Inferences

- dns: 共享主机 + 独立邮件配置通常意味着电商团队运维预算有限。
- headers: 无 CDN 且响应慢，会同时影响安全、转化率和 SEO。
- email: 无 DMARC 的电商域名很容易被仿冒发货/退款邮件。
- tech: WordPress 插件面和支付链路并存，适合做插件治理和交易安全评估。
