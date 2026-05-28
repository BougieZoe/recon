import subprocess
import sys
import re
import io
import socket
import contextvars
from datetime import datetime

# ==================== 颜色定义 ====================
RESET = '\033[0m'
BOLD = '\033[1m'
GREEN = '\033[92m'
CYAN = '\033[96m'
AMBER = '\033[93m'
RED = '\033[91m'
DIM = '\033[2m'
PURPLE = '\033[95m'

# ==================== 工具函数 ====================
def strip_ansi(text):
    return re.sub(r'\033\[[0-9;]*m', '', str(text))

def c(text, color):
    """全局快捷颜色函数（推荐在简单场景使用）"""
    return f"{color}{text}{RESET}"

def run(cmd, timeout=12):
    """执行系统命令"""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout + r.stderr
    except subprocess.TimeoutExpired:
        return "[timeout]"
    except Exception as e:
        return f"[error: {e}]"

def check_tool(name):
    """检查命令是否存在"""
    import shutil
    return shutil.which(name) is not None

def check_port(host, port, timeout=3):
    """检查端口是否开放"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect((host, port))
            return True
    except:
        return False

def banner():
    print(c("""
 ██████╗ ███████╗ ██████╗ ██████╗ ███╗  ██╗
 ██╔══██╗██╔════╝██╔════╝██╔═══██╗████╗ ██║
 ██████╔╝█████╗  ██║     ██║   ██║██╔██╗██║
 ██╔══██╗██╔══╝  ██║     ██║   ██║██║╚████║
 ██║  ██║███████╗╚██████╗╚██████╔╝██║ ╚███║
 ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚╝
    """, GREEN))
    print(c("  被动情报分析工具  Passive Recon CLI\n", DIM))

# ==================== 核心输出类 ====================
class ModuleOutput:
    def __init__(self, module_name: str, json_mode: bool = False):
        self.module = module_name
        self.json_mode = json_mode
        self.buffer = io.StringIO() if not json_mode else None
        self.findings = []

    def section(self, title: str):
        if self.json_mode:
            return
        self.buffer.write(f"\n{c('──────────────────────────────────────', DIM)}\n")
        self.buffer.write(f"  {c('◈', CYAN)} {c(title, BOLD)}\n")
        self.buffer.write(c('──────────────────────────────────────', DIM))

    def row(self, label: str, value, risk: str = 'info'):
        colors = {'low': GREEN, 'info': CYAN, 'medium': AMBER, 'high': RED}
        color = colors.get(risk, CYAN)
        
        clean_val = strip_ansi(value)
        self.findings.append({"label": label, "value": clean_val, "risk": risk})
        
        if not self.json_mode and self.buffer:
            self.buffer.write(
                f"\n  {c('●', color)} {c(label.ljust(18), DIM)} {value}"
            )

    def inference(self, text: str, color=PURPLE):
        self.findings.append({"type": "inference", "text": strip_ansi(text)})
        if not self.json_mode and self.buffer:
            self.buffer.write(
                f"\n  {c('│', color)} {c('推理：', BOLD)}{c(text, DIM)}\n"
            )

    def raw(self, text: str):
        if not self.json_mode and self.buffer:
            self.buffer.write(text)

    def get_output(self) -> str:
        if not self.json_mode and self.buffer:
            return self.buffer.getvalue()
        return ""

    def to_dict(self) -> dict:
        d = {"findings": []}
        inferences = []
        for f in self.findings:
            if f.get("type") == "inference":
                inferences.append(f["text"])
            else:
                d["findings"].append(f)
        if inferences:
            d["inferences"] = inferences
        return d

# ==================== 每次扫描隔离的上下文 ====================
class ScanContext:
    def __init__(self):
        self._var = contextvars.ContextVar("recon_context", default=None)

    def set(self, value=None):
        ctx = {} if value is None else value
        self._var.set(ctx)
        return ctx

    def current(self):
        ctx = self._var.get()
        if ctx is None:
            ctx = {}
            self._var.set(ctx)
        return ctx

    def clear(self):
        self.current().clear()

    def get(self, key, default=None):
        return self.current().get(key, default)

    def __setitem__(self, key, value):
        self.current()[key] = value

    def __getitem__(self, key):
        return self.current()[key]

    def __contains__(self, key):
        return key in self.current()


CONTEXT = ScanContext()
