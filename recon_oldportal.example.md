# RECON - oldportal.example

- Generated: 2026-05-29 01:00:25
- Elapsed: 3.1s
- Overall: 30/100
- Risk counts: high=8, medium=5, low=0, info=1

## Scores

- Security: 0/100
- Email: 45/100
- Infrastructure: 50/100
- Tech Debt: 40/100

## Priority Actions

- [高] dns / SPF: 未配置 ✗
  Evidence: DNS / dig
  Recommendation: 收敛 SPF include，最终使用 -all，避免域名被仿冒发信。
- [高] dns / 托管: Lolipop 共享主机
  Evidence: DNS / dig
  Recommendation: 优先确认真实性、责任人和修复窗口，避免该信号进入客户安全评审。
- [高] dns / 邮件服务: 未配置 MX
  Evidence: DNS / dig
  Recommendation: 优先确认真实性、责任人和修复窗口，避免该信号进入客户安全评审。
- [高] email / DMARC: 未配置 ✗
  Evidence: DNS TXT records
  Recommendation: 将 DMARC 从 none 推进到 quarantine/reject，并确认 rua 报告链路可用。
- [高] headers / CDN: 无CDN ⚠ DDoS裸奔
  Evidence: HTTP response headers
  Recommendation: 接入 CDN/WAF，并确认源站不直接暴露在公网。

## Findings

### dns - SPF
- Risk: 高
- Value: 未配置 ✗
- Evidence: DNS / dig
- Recommendation: 收敛 SPF include，最终使用 -all，避免域名被仿冒发信。

### dns - 托管
- Risk: 高
- Value: Lolipop 共享主机
- Evidence: DNS / dig
- Recommendation: 优先确认真实性、责任人和修复窗口，避免该信号进入客户安全评审。

### dns - 邮件服务
- Risk: 高
- Value: 未配置 MX
- Evidence: DNS / dig
- Recommendation: 优先确认真实性、责任人和修复窗口，避免该信号进入客户安全评审。

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

### headers - X-Powered-By
- Risk: 高
- Value: PHP/7.4 ⚠ EOL!
- Evidence: HTTP response headers
- Recommendation: 升级 EOL 运行时，并隐藏版本泄露 header。

### headers - 安全响应头
- Risk: 高
- Value: 缺失 7/7 项
- Evidence: HTTP response headers
- Recommendation: 补齐 CSP、HSTS、X-Content-Type-Options、Referrer-Policy 等安全响应头。

### tech - CRM/客服
- Risk: 高
- Value: 未检测到
- Evidence: Homepage HTML fingerprint
- Recommendation: 优先确认真实性、责任人和修复窗口，避免该信号进入客户安全评审。

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
- Value: Apache 2.4
- Evidence: HTTP response headers
- Recommendation: 纳入近期加固计划，并在下一轮扫描中复核。

### ssl - SSL 检查
- Risk: 中
- Value: 443 端口未开放
- Evidence: TLS handshake / crt.sh
- Recommendation: 纳入近期加固计划，并在下一轮扫描中复核。

### tech - CMS
- Risk: 中
- Value: WordPress
- Evidence: Homepage HTML fingerprint
- Recommendation: 纳入近期加固计划，并在下一轮扫描中复核。

### dns - IPv4
- Risk: 信息
- Value: 192.0.2.80
- Evidence: DNS / dig
- Recommendation: 保留为资产画像证据，后续用于趋势对比。

## Inferences

- dns: 共享主机 + 邮件记录缺失，通常意味着长期无人维护。
- headers: PHP 7.x EOL + 安全响应头全缺失，是典型遗留门户风险组合。
- email: 邮件认证记录缺失，外部人员可轻易仿冒该域名发信。
- tech: 无 CRM/客服工具，销售或支持流程可能高度人工化。
