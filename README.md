<p align="center">
  <img src="https://img.shields.io/badge/RECON-Passive%20Intel-%2322d3ee?style=flat-square" alt="RECON">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square" alt="Python">
  <img src="https://img.shields.io/badge/Hackathon-Ready-brightgreen?style=flat-square" alt="Hackathon">
</p>

<h1 align="center">🔍 RECON</h1>
<p align="center"><b>Passive Intelligence CLI — 被动情报分析工具</b></p>
<p align="center">输入一个域名，输出一份可落地的商业 + 技术情报。</p>

---

## Why RECON

在销售、投资、竞品分析场景中，你需要快速了解一家公司的技术栈、安全水平、工程成熟度——但又不能扫端口、不能发请求、不能触碰法律红线。

RECON 只用 **公开 DNS / WHOIS / 证书透明度日志** 等被动源，5 秒内输出：
- 他们用什么技术（CMS / 框架 / CDN / 第三方服务）
- 他们的安全水平（SSL / 安全响应头 / DMARC）
- 他们的工程团队实力（子域名数量 = 业务线、有无 dev/staging）
- 他们的商业画像（中小企 / SaaS / 电商 / 遗留项目）

## Quick Start

```bash
# Docker（推荐，零依赖）
docker build -t recon ~/.recon
docker run --rm recon example.com --report html

# macOS 原生
python3 ~/.recon/recon.py example.com
```

## Usage

```bash
# 单域名扫描
recon example.com

# 所有模块 + 深度分析
recon example.com --analyze

# 并行扫描（快 3×）
recon example.com --parallel --analyze

# 导出 HTML 报告
recon example.com --report html && open recon_example.com.html

# 批量比较多个域名
recon example.com example.org --batch

# 离线演示（不用网络，适合现场展示）
recon --demo --report html
recon --demo --demo-profile legacy

# 交互终端模式
recon -i

# JSON 输出 + 保存到文件
recon example.com --json --output scan.json

# 查看 / 比较历史扫描
recon --history
recon --diff 1 2

# Web UI
recon --web
```

## Modules

| 模块 | 功能 | 数据源 |
|------|------|--------|
| `dns` | A/AAAA/MX/NS/TXT/SOA + 托管识别 | dig |
| `ssl` | 颁发机构 / 过期 / 子域名 / TLS 版本 | openssl, crt.sh |
| `headers` | 安全响应头 / CDN / CORS / HTTP 版本 | curl |
| `email` | SPF/DKIM/DMARC/MTA-STS | dig |
| `tech` | CMS / 框架 / 第三方服务指纹 | 响应头 + 页面特征 |
| `basics` | www 重定向 / 端口扫描 | socket |
| `subdomain` | 子域名枚举 | crt.sh |
| `wayback` | 历史快照 | Wayback Machine CDX |
| `email_harvest` | 邮件地址收集 | 页面 + PGP |
| `leak_search` | 泄露搜索 | HIBP + GitHub |
| `asn_ip` | IP 归属 / ASN / VT 检测 | Team Cymru + dig |

## Scoring

5 维度加权评分（0-100）：

```
总体 = 安全×35% + 基建×25% + 邮件×20% + 技术债×20%
```

- **安全**: DMARC / SSL 证书 / 安全响应头 / CDN
- **基建**: 托管商 / CDN / IPv6 / DNS 冗余
- **邮件**: DMARC 策略 / DKIM / SPF -all
- **技术债**: PHP 版本 / 过期组件 / 免费证书

## Architecture

```
~/.recon/
├── recon.py         ← 入口（5 行）
├── recon/           ← 主包（21 文件）
│   ├── core.py      ← ModuleOutput, ANSI 颜色, 工具
│   ├── cli.py       ← CLI 解析 + 交互模式
│   ├── analysis.py  ← 评分引擎 + 商业洞察
│   ├── report.py    ← HTML / Markdown 报告
│   ├── history.py   ← SQLite 历史
│   ├── webapp.py    ← Streamlit Web UI
│   ├── ssl.py       ← SSL/TLS 扫描
│   ├── dns.py       ← DNS 记录扫描
│   ├── headers.py   ← HTTP 响应头
│   ├── email.py     ← 邮件安全
│   ├── tech.py      ← 技术指纹
│   ├── basics.py    ← 基础检查
│   ├── subdomain.py ← 子域名
│   ├── wayback.py   ← 历史快照
│   ├── email_harvest.py
│   ├── leak_search.py
│   ├── asn_ip.py
│   ├── knowledge.py ← 行业知识库
│   ├── config.py    ← API Key 配置
│   ├── rules.py     ← 推理规则
│   └── demo.py      ← 离线演示数据
├── modules/         ← 用户插件
├── Dockerfile
└── requirements.txt
```

## Hackathon Notes

- **演示**: `recon --demo --report html && open recon_*.html` — 完全离线，零翻车风险
- **Key 差异**: 无需任何 API Key，所有数据来自公开源
- **Web UI**: `recon --web` 启动 Streamlit 仪表盘
- **技术栈**: 纯 Python 3 + stdlib，外部依赖仅 openssl/dig/whois（Docker 已包含）

---

<p align="center"><i>Built for Hackathon · Passive Reconnaissance · AGI-powered Insights</i></p>
