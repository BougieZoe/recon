"""
RECON Web UI — Streamlit 快速原型
启动: recon --web
"""
import sys, os, json, re
from datetime import datetime

sys.path.insert(0, os.path.expanduser("~/.recon"))

def run_web():
    try:
        import streamlit as st
    except ImportError:
        print("请先安装 streamlit: pip3 install streamlit --break-system-packages")
        return

    from recon.cli import BUILTIN_SCANNERS, load_plugins, _scan_domain
    from recon.core import c, strip_ansi
    from recon.analysis import compute_all_scores, run_analysis
    from recon.rules import load_rules
    from recon.config import load_config
    from recon.knowledge import load_knowledge, advice_section, detect_industry
    from recon.report import generate_html, generate_markdown
    from recon.demo import DEFAULT_PROFILE, get_demo_scan, list_profiles

    load_rules()
    load_config()
    load_knowledge()

    all_scanners = {**BUILTIN_SCANNERS, **load_plugins()}

    st.set_page_config(page_title="RECON Web", layout="wide")
    st.markdown("""
    <style>
    .stApp { background: #0f172a; color: #e2e8f0; }
    .stTextInput>div>div>input { background: #1e293b; color: #e2e8f0; border: 1px solid #334155; }
    .stTextInput>label { color: #94a3b8; }
    h1, h2, h3 { color: #22d3ee !important; }
    .st-bd { background: #1e293b; }
    .stButton>button { background: #22d3ee; color: #0f172a; font-weight: bold; border: none; }
    .stButton>button:hover { background: #06b6d4; }
    </style>
    """, unsafe_allow_html=True)

    st.title("🔍 RECON Web")
    st.caption("Passive Intelligence · 被动情报分析")

    col1, col2, col3 = st.columns([3, 1.6, 1.2])
    with col1:
        domain_input = st.text_input("目标域名", placeholder="example.co.jp（Demo 可留空）")
    with col2:
        modules_select = st.multiselect("模块", list(all_scanners.keys()), default=["dns","ssl","headers","email","tech","basics","asn_ip"])
    with col3:
        demo_mode = st.checkbox("Demo 模式", value=False)
        demo_profile = st.selectbox("画像", list_profiles(), index=list_profiles().index(DEFAULT_PROFILE))

    if st.button("🚀 开始扫描", type="primary", use_container_width=True) and (domain_input or demo_mode):
        domain = re.sub(r'^https?://', '', domain_input).split('/')[0].strip() if domain_input else None
        if domain and not re.match(r'^[a-zA-Z0-9._-]+\.[a-zA-Z]{2,}$', domain):
            st.error("域名格式不正确")
            return

        mods = modules_select if modules_select else list(all_scanners.keys())
        start = datetime.now()
        if demo_mode:
            domain, results, elapsed = get_demo_scan(domain, demo_profile, mods)
        else:
            with st.spinner(f"正在扫描 {domain} ..."):
                results = _scan_domain(domain, mods, all_scanners, json_mode=True, parallel=True)
                elapsed = (datetime.now() - start).total_seconds()

        st.success(f"{'Demo 已加载' if demo_mode else '扫描完成'} ({elapsed:.1f}s)")

        # Scores
        scores = compute_all_scores(results)
        sc1, sc2, sc3, sc4, sc5 = st.columns(5)
        labels = [("总体", "overall"), ("安全", "security"), ("基础设施","infrastructure"), ("邮件","email"), ("技术债","techdebt")]
        for col, (label, key) in zip([sc1,sc2,sc3,sc4,sc5], labels):
            s = scores.get(key, 0)
            color = "#22c55e" if s >= 70 else "#f59e0b" if s >= 40 else "#ef4444"
            col.metric(label, f"{s}/100", delta_color="inverse")
            col.markdown(f"<div style='height:8px;background:#1e293b;border-radius:4px'><div style='height:8px;width:{s}%;background:{color};border-radius:4px'></div></div>", unsafe_allow_html=True)

        # Knowledge advice
        ind = detect_industry(results)
        with st.expander(f"💡 行业建议 · {ind}", expanded=True):
            from recon.knowledge import get_advice
            advice = get_advice(ind)
            if advice:
                st.caption(advice.get("description", ""))
                for item in advice.get("checklist", []):
                    risk = item.get("risk", "medium")
                    emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(risk, "⚪")
                    st.markdown(f"{emoji} {item.get('text', '')}")

        # Results by module
        for mod_name, mod_data in results.items():
            findings = mod_data.get("findings", [])
            inferences = mod_data.get("inferences", [])
            if not findings and not inferences: continue
            with st.expander(f"◈ {mod_name}", expanded=False):
                for f in findings:
                    risk = f.get("risk", "info")
                    emoji = {"high": "🔴", "medium": "🟡", "low": "🟢", "info": "ℹ️"}.get(risk, "ℹ️")
                    st.markdown(f"{emoji} **{f.get('label', '')}**: {f.get('value', '')}")
                for inf in inferences:
                    st.markdown(f"> 💬 {inf}")

        # Downloads
        h1, h2 = st.columns(2)
        with h1:
            html = generate_html(domain, results, elapsed)
            st.download_button("📄 下载 HTML 报告", html, f"recon_{domain}.html", "text/html", use_container_width=True)
        with h2:
            md = generate_markdown(domain, results, elapsed)
            st.download_button("📝 下载 Markdown 报告", md, f"recon_{domain}.md", "text/markdown", use_container_width=True)

        # Raw JSON
        with st.expander("📦 原始 JSON"):
            st.json({"domain": domain, "timestamp": start.isoformat(), "elapsed": round(elapsed, 2), "mode": "demo" if demo_mode else "live", "modules": results})
