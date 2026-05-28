import sys, re, json, os, argparse, contextvars
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from .core import c, banner, ModuleOutput, CONTEXT, RED, CYAN, DIM, GREEN, BOLD, AMBER, PURPLE
from .rules import load_rules
from .config import load_config
from . import analysis
from .demo import DEFAULT_PROFILE, get_demo_scan, list_profiles

import recon.dns, recon.ssl, recon.headers, recon.email, recon.tech
import recon.basics, recon.subdomain, recon.wayback
import recon.email_harvest, recon.leak_search, recon.asn_ip

BUILTIN_SCANNERS = {
    'dns': recon.dns.scan, 'ssl': recon.ssl.scan, 'headers': recon.headers.scan,
    'email': recon.email.scan, 'tech': recon.tech.scan, 'basics': recon.basics.scan,
    'subdomain': recon.subdomain.scan, 'wayback': recon.wayback.scan,
    'email_harvest': recon.email_harvest.scan, 'leak_search': recon.leak_search.scan,
    'asn_ip': recon.asn_ip.scan,
}

def load_plugins():
    scanners = {}
    plugin_dir = os.path.expanduser("~/.recon/modules")
    if not os.path.isdir(plugin_dir): return scanners
    sys.path.insert(0, plugin_dir)
    for f in sorted(os.listdir(plugin_dir)):
        if f.endswith(".py") and not f.startswith("_"):
            name = f[:-3]
            try:
                import importlib
                mod = importlib.import_module(name)
                if hasattr(mod, "scan"): scanners[name] = mod.scan
            except: pass
    return scanners

def _scan_domain(domain, mods, all_scanners, json_mode, parallel):
    CONTEXT.set({})
    results = {}
    if parallel and len(mods) > 1:
        outputs = {}
        parallel_mods = list(mods)

        # dns populates CONTEXT["hosting"]; run it first so ssl/header hints are stable.
        if "dns" in parallel_mods:
            o = ModuleOutput("dns", json_mode=json_mode)
            try:
                all_scanners["dns"](domain, o)
            except Exception as e:
                if json_mode:
                    o.findings.append({"type": "inference", "text": f"模块 dns 出错: {e}"})
                else:
                    o.raw(c(f"\n  ✗ 模块 dns 出错: {e}", RED))
            outputs["dns"] = o
            results["dns"] = o.to_dict()
            parallel_mods.remove("dns")

        with ThreadPoolExecutor(max_workers=len(mods)) as ex:
            def run_mod(m):
                o = ModuleOutput(m, json_mode=json_mode)
                try:
                    all_scanners[m](domain, o)
                except Exception as e:
                    if json_mode:
                        o.findings.append({"type": "inference", "text": f"模块 {m} 出错: {e}"})
                    else:
                        o.raw(c(f"\n  ✗ 模块 {m} 出错: {e}", RED))
                return m, o
            futures = {}
            for m in parallel_mods:
                ctx = contextvars.copy_context()
                futures[ex.submit(ctx.run, run_mod, m)] = m
            for f in as_completed(futures):
                m, o = f.result(); outputs[m] = o; results[m] = o.to_dict()
        if not json_mode:
            for m in mods:
                t = outputs[m].get_output()
                if t: print(t, end='')
    else:
        for m in mods:
            o = ModuleOutput(m, json_mode=json_mode)
            try: all_scanners[m](domain, o)
            except Exception as e:
                if json_mode: o.findings.append({"type": "inference", "text": f"模块 {m} 出错: {e}"})
                else: o.raw(c(f"\n  ✗ 模块 {m} 出错: {e}", RED))
            results[m] = o.to_dict()
            if not json_mode:
                t = o.get_output()
                if t: print(t, end='')
    return results

def _print_summary(domain, start, elapsed):
    print(f"\n{c('──────────────────────────────────────', DIM)}")
    print(f"  {c('◈', CYAN)} {c(f'情报摘要 · {domain}', BOLD)}")
    print(c('──────────────────────────────────────', DIM))
    print(f"\n  {c('扫描完成', GREEN)} · {c(datetime.now().strftime('%Y-%m-%d %H:%M'), DIM)}{c(f'  ({elapsed:.1f}s)', DIM)}")
    print(f"\n{c('═'*40, DIM)}\n")

def _print_cached_results(results):
    colors = {'low': GREEN, 'info': CYAN, 'medium': AMBER, 'high': RED}
    for module, data in results.items():
        print(f"\n{c('──────────────────────────────────────', DIM)}")
        print(f"  {c('◈', CYAN)} {c(module.upper(), BOLD)}")
        print(c('──────────────────────────────────────', DIM))
        for f in data.get("findings", []):
            risk = f.get("risk", "info")
            color = colors.get(risk, CYAN)
            print(f"  {c('●', color)} {c(str(f.get('label', '')).ljust(18), DIM)} {f.get('value', '')}")
        for inf in data.get("inferences", []):
            print(f"  {c('│', PURPLE)} {c('推理：', BOLD)}{c(inf, DIM)}")

def _normalize_domain(text):
    text = text.strip()
    text = re.sub(r'^https?://', '', text)
    return text.split('/')[0].strip()

def _valid_domain(domain):
    return bool(re.match(r'^[a-zA-Z0-9._-]+\.[a-zA-Z]{2,}$', domain or ""))

def _write_reports(domain, results, elapsed, report_kind, base_path=None):
    if not report_kind:
        return []
    from . import report
    paths = []
    base = base_path or f"recon_{domain}"
    if report_kind == 'md':
        md_path = base + '.md'
        with open(md_path, 'w') as f:
            f.write(report.generate_markdown(domain, results, elapsed))
        paths.append(md_path)
    return paths

def _interactive_help(all_scanners, current_modules, parallel, report_kind):
    print(c("\n可直接粘贴公司链接或域名开始扫描：", BOLD))
    print(f"  {c('https://example.com', CYAN)}")
    print(f"  {c('example.com', CYAN)}")
    print(c("\n常用命令：", BOLD))
    print("  demo [saas|commerce|legacy]  使用离线演示数据")
    print("  modules                      查看当前模块")
    print("  modules default              使用推荐模块")
    print("  modules all                  使用全部模块")
    print("  modules dns,headers,email    指定模块")
    print("  parallel on|off              开关并行扫描")
    print("  report on|off                扫描后自动生成 Markdown 报告")
    print("  help                         显示帮助")
    print("  quit                         退出")
    print(c("\n当前设置：", BOLD))
    print(f"  modules: {', '.join(current_modules)}")
    print(f"  parallel: {'on' if parallel else 'off'}")
    print(f"  report: {report_kind or 'off'}")
    print(f"  available: {', '.join(all_scanners.keys())}\n")

def run_interactive():
    plugin_scanners = load_plugins()
    all_scanners = {**BUILTIN_SCANNERS, **plugin_scanners}
    default_modules = [m for m in ["dns", "ssl", "headers", "email", "tech", "basics", "asn_ip"] if m in all_scanners]
    modules = list(default_modules)
    parallel = True
    report_kind = None

    banner()
    print(c("  交互模式：粘贴公司链接或域名后回车即可扫描。输入 help 查看命令。\n", DIM))

    while True:
        try:
            line = input(c("recon> ", CYAN)).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not line:
            continue

        lower = line.lower()
        if lower in ("q", "quit", "exit"):
            return
        if lower in ("h", "help", "?"):
            _interactive_help(all_scanners, modules, parallel, report_kind)
            continue
        if lower == "modules":
            print(f"当前模块: {c(', '.join(modules), CYAN)}")
            print(f"可用模块: {c(', '.join(all_scanners.keys()), DIM)}")
            continue
        if lower.startswith("modules "):
            value = line.split(None, 1)[1].strip()
            if value == "default":
                modules = list(default_modules)
            elif value == "all":
                modules = list(all_scanners.keys())
            else:
                requested = [m.strip() for m in value.split(',') if m.strip()]
                unknown = [m for m in requested if m not in all_scanners]
                if unknown:
                    print(c(f"未知模块: {', '.join(unknown)}", RED))
                    continue
                modules = requested
            print(f"模块已设置: {c(', '.join(modules), CYAN)}")
            continue
        if lower.startswith("parallel "):
            value = lower.split(None, 1)[1].strip()
            if value not in ("on", "off"):
                print(c("用法: parallel on|off", AMBER))
                continue
            parallel = value == "on"
            print(f"parallel: {c(value, GREEN if parallel else AMBER)}")
            continue
        if lower.startswith("report "):
            value = lower.split(None, 1)[1].strip()
            if value == "off":
                report_kind = None
            elif value == "on":
                report_kind = "md"
            else:
                print(c("用法: report on|off", AMBER))
                continue
            print(f"report: {c(report_kind or 'off', CYAN)}")
            continue

        start = datetime.now()
        if lower.startswith("demo"):
            parts = line.split()
            profile = parts[1] if len(parts) > 1 else DEFAULT_PROFILE
            if profile not in list_profiles():
                print(c(f"未知 demo profile: {profile}", RED))
                continue
            domain, results, elapsed = get_demo_scan(None, profile, modules)
            print(f"\n  目标: {c(domain, CYAN)}")
            print(f"  时间: {c(start.strftime('%Y-%m-%d %H:%M:%S'), DIM)}")
            print(f"  模式: {c(f'Demo / Offline · {profile}', AMBER)}")
            _print_cached_results(results)
        else:
            domain = _normalize_domain(line)
            if not _valid_domain(domain):
                print(c("请输入有效域名或链接，例如 https://example.com", RED))
                continue
            print(f"\n  目标: {c(domain, CYAN)}")
            print(f"  时间: {c(start.strftime('%Y-%m-%d %H:%M:%S'), DIM)}")
            results = _scan_domain(domain, modules, all_scanners, False, parallel)
            elapsed = (datetime.now() - start).total_seconds()

        _print_summary(domain, start, elapsed)
        paths = _write_reports(domain, results, elapsed, report_kind)
        for path in paths:
            print(c(f"  报告: {path}", GREEN))

def main():
    parser = argparse.ArgumentParser(description='RECON - Passive Intelligence CLI')
    parser.add_argument('domains', nargs='*', help='目标域名 (多个域名用空格分隔)')
    parser.add_argument('--modules', default=None, help='扫描模块 (默认: 全部)')
    parser.add_argument('--json', action='store_true', help='JSON 格式输出')
    parser.add_argument('--parallel', action='store_true', help='并行扫描（更快）')
    parser.add_argument('--output', help='输出到文件')
    parser.add_argument('--analyze', action='store_true', help='深度分析：五轴推理 + 信号矩阵')
    parser.add_argument('--report', choices=['md'], help='导出 Markdown 报告')
    parser.add_argument('--batch', action='store_true', help='批量模式：输出对比表格')
    parser.add_argument('--save', action='store_true', help='保存扫描到历史记录')
    parser.add_argument('--history', action='store_true', help='查看历史扫描记录')
    parser.add_argument('--diff', nargs=2, metavar=('ID1', 'ID2'), help='比较两次历史扫描')
    parser.add_argument('--web', action='store_true', help='启动 Web UI')
    parser.add_argument('--demo', action='store_true', help='使用内置演示数据，不发起网络请求')
    parser.add_argument('--demo-profile', choices=list_profiles(), default=DEFAULT_PROFILE, help='演示数据画像')
    parser.add_argument('-i', '--interactive', action='store_true', help='启动终端交互模式')
    args = parser.parse_args()

    load_rules()
    load_config()

    # Route subcommands that don't need domains
    if args.web:
        from .webapp import run_web
        run_web()
        return

    if args.interactive:
        run_interactive()
        return

    if args.history:
        from .history import list_history
        list_history()
        return

    if args.diff:
        from .history import diff_scans
        diff_scans(args.diff[0], args.diff[1])
        return

    if args.demo and not args.domains:
        args.domains = []
    elif not args.domains:
        parser.print_help()
        sys.exit(1)

    plugin_scanners = load_plugins()
    all_scanners = {**BUILTIN_SCANNERS, **plugin_scanners}

    if args.modules:
        mods = [m.strip() for m in args.modules.split(',') if m.strip() in all_scanners]
    else:
        mods = list(all_scanners.keys())
    if not mods:
        print(c("错误：没有可用的扫描模块", RED)); sys.exit(1)

    domains = [re.sub(r'^https?://', '', d).split('/')[0].strip() for d in args.domains]
    if args.demo and not domains:
        domains = list_profiles() if args.batch else [None]
    bad = [d for d in domains if d and not re.match(r'^[a-zA-Z0-9._-]+\.[a-zA-Z]{2,}$', d) and not args.demo]
    if bad:
        print(c(f"错误：无效域名 {bad}", RED)); sys.exit(1)

    is_batch = args.batch or len(domains) > 1

    if is_batch:
        batch_results = {}
        for i, domain in enumerate(domains):
            start = datetime.now()
            print(f"\n{c('═'*50, BOLD)}")
            display_domain = domain or args.demo_profile
            print(f"  {c(f'[{i+1}/{len(domains)}]', CYAN)} {c(display_domain, BOLD)}")
            print(c('═'*50, BOLD))
            if args.demo:
                domain, results, elapsed = get_demo_scan(domain, domain if args.batch else args.demo_profile, mods)
                _print_cached_results(results)
            else:
                results = _scan_domain(domain, mods, all_scanners, False, args.parallel)
                elapsed = (datetime.now() - start).total_seconds()
            _print_summary(domain, start, elapsed)
            scores = analysis.compute_all_scores(results)
            batch_results[domain] = {"results": results, "scores": scores, "elapsed": elapsed}

            if args.save:
                from .history import save_scan
                save_scan(domain, results, elapsed)

        print(f"\n{c('═'*56, BOLD)}")
        print(f"  {c('批量对比 ·', BOLD)} {c(f'{len(domains)} 个域名', CYAN)}")
        print(c('═'*56, BOLD))
        print(f"  {c('域名'.ljust(22), DIM)} {'总体'.ljust(8)} {'安全'.ljust(7)} {'基建'.ljust(7)} {'邮件'.ljust(7)} {'技术债'.ljust(7)} {'耗时'}")
        print(c('─'*56, DIM))
        for d in list(batch_results.keys()):
            scores = batch_results[d]["scores"]
            s = scores["overall"]
            color = GREEN if s >= 70 else AMBER if s >= 40 else RED
            e = batch_results[d]["elapsed"]
            print(f"  {c(d[:20].ljust(22), color)} "
                  f"{c(str(scores.get('overall',0)).rjust(4)+'/100', color)} "
                  f"{c(str(scores.get('security',0)).rjust(3), GREEN if scores.get('security',0)>=70 else AMBER)} "
                  f"{c(str(scores.get('infrastructure',0)).rjust(3), GREEN if scores.get('infrastructure',0)>=70 else AMBER)} "
                  f"{c(str(scores.get('email',0)).rjust(3), GREEN if scores.get('email',0)>=70 else AMBER)} "
                  f"{c(str(scores.get('techdebt',0)).rjust(3), GREEN if scores.get('techdebt',0)>=70 else AMBER)} "
                  f"{c(f'{e:.1f}s', DIM)}")
        print(c('─'*56, DIM))
        print()
    else:
        domain = domains[0]
        start = datetime.now()
        cached_demo = None
        if args.demo:
            domain, results, elapsed = get_demo_scan(domain, args.demo_profile, mods)
            cached_demo = (results, elapsed)

        if not args.json:
            banner()
            print(f"  目标: {c(domain, CYAN)}")
            print(f"  时间: {c(start.strftime('%Y-%m-%d %H:%M:%S'), DIM)}")
            if args.demo:
                print(f"  模式: {c(f'Demo / Offline · {args.demo_profile}', AMBER)}")

        if args.demo:
            results, elapsed = cached_demo
            if not args.json:
                _print_cached_results(results)
        else:
            results = _scan_domain(domain, mods, all_scanners, args.json, args.parallel)
            elapsed = (datetime.now() - start).total_seconds()
        output = {
            "domain": domain,
            "timestamp": start.isoformat(),
            "elapsed": round(elapsed, 2),
            "modules": results,
            "mode": "demo" if args.demo else "live",
        }

        if args.analyze and not args.json:
            analysis.run_analysis(domain, results, elapsed)

        if args.json:
            text = json.dumps(output, indent=2, ensure_ascii=False)
            print(text)
        else:
            _print_summary(domain, start, elapsed)

        if args.output:
            with open(args.output, 'w') as f:
                json.dump(output, f, indent=2, ensure_ascii=False)

        if args.report and not args.json:
            from . import report
            md = report.generate_markdown(domain, results, elapsed)
            md_path = args.output + '.md' if args.output else f"recon_{domain}.md"
            with open(md_path, 'w') as f: f.write(md)
            if not args.output: print(c(f"  MD 报告: {md_path}", GREEN))

        if args.save:
            from .history import save_scan
            save_scan(domain, results, elapsed)

if __name__ == '__main__':
    main()
