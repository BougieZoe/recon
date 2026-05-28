import json
from datetime import datetime
from pathlib import Path

def generate_html_report(data, output_path=None):
    if output_path is None:
        output_path = f"recon_report_{data['domain']}_{datetime.now().strftime('%Y%m%d_%H%M')}.html"
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>RECON - {data['domain']}</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 20px; }}
        .header {{ text-align: center; padding: 20px; background: #1e2937; border-radius: 12px; }}
        .module {{ background: #1e2937; margin: 20px 0; padding: 20px; border-radius: 12px; }}
        .high {{ border-left: 5px solid #ef4444; }}
        .medium {{ border-left: 5px solid #f59e0b; }}
        .finding {{ display: flex; justify-content: space-between; margin: 12px 0; }}
        .tag {{ padding: 4px 12px; border-radius: 9999px; font-size: 0.85em; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 RECON - 被动情报分析报告</h1>
        <p>目标: <strong>{data['domain']}</strong> | 时间: {data['timestamp']}</p>
    </div>
"""
    # 这里可以继续扩展每个 module 的 HTML 生成逻辑...
    html += "<h2>扫描完成</h2></body></html>"
    
    Path(output_path).write_text(html, encoding='utf-8')
    return output_path
