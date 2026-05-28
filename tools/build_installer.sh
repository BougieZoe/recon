#!/usr/bin/env bash
# RECON 跨平台自解压安装包生成器
# 用法: bash tools/build_installer.sh
# 输出: dist/recon_installer.sh

set -e
cd "$(dirname "$0")/.."
mkdir -p dist

# 收集文件
FILES=$(find recon.py recon modules -type f \
  ! -path '*__pycache__*' ! -name '*.pyc' ! -name '*.html' ! -name '*.md' \
  ! -name 'history.db' ! -name 'config.yaml' \
  | sort)

# 打成 tar + gzip + base64
PAYLOAD=$(tar czf - $FILES | base64)

# 生成安装器（payload 占位符在 build 阶段替换）
cat > dist/recon_installer.sh << 'INSTALLER'
#!/usr/bin/env bash
# RECON 一键安装器 — 支持 macOS / Linux / Termux
set -e
INSTALL_DIR="$HOME/.recon"
BIN_DIR="$HOME/.local/bin"

case "$(uname -s)" in
  Darwin) PLATFORM="macos" ;;
  Linux)
    if [ -f /data/data/com.termux/files/usr/bin/bash ]; then PLATFORM="termux"; BIN_DIR="$HOME/bin"
    else PLATFORM="linux"; fi ;;
esac

echo "📦 RECON Installer · $PLATFORM"

# 安装系统依赖
case "$PLATFORM" in
  macos)
    if ! command -v brew &>/dev/null; then echo "请先安装 Homebrew: https://brew.sh"; exit 1; fi
    command -v python3 &>/dev/null || brew install python3
    for c in openssl dig whois; do command -v $c &>/dev/null || brew install $c; done
    ;;
  termux)
    pkg update -y 2>/dev/null
    pkg install -y python openssl-tool dnsutils whois curl 2>/dev/null
    ;;
esac

mkdir -p "$INSTALL_DIR"

echo "📄 解压中..."
python3 -c "
import base64, gzip, tarfile, io, os, sys

with open(sys.argv[1], 'r') as f:
    content = f.read()

marker = content.rfind('\x5f\x5fPAYLOAD_BELOW\x5f\x5f')
if marker < 0:
    sys.exit('安装包损坏：找不到 payload')

payload = content[marker + len('\x5f\x5fPAYLOAD_BELOW\x5f\x5f'):].strip()
raw = base64.b64decode(payload)
out = sys.argv[2]

with tarfile.open(fileobj=io.BytesIO(gzip.decompress(raw))) as t:
    t.extractall(out)
" "$0" "$INSTALL_DIR"

mkdir -p "$BIN_DIR"
cat > "$BIN_DIR/recon" << 'WRAPPER'
#!/bin/sh
PYTHONPATH="$HOME/.recon" exec python3 "$HOME/.recon/recon.py" "$@"
WRAPPER
chmod +x "$BIN_DIR/recon"
chmod +x "$INSTALL_DIR/recon.py"

echo ""
echo "✅ RECON 安装完成！"
echo "   运行: recon example.com"
echo "   演示: recon --demo"
echo ""
echo "   如果 '$BIN_DIR' 不在 PATH 中，执行:"
echo "   echo 'export PATH=\"$BIN_DIR:\$PATH\"' >> ~/.bashrc && source ~/.bashrc"
exit 0
INSTALLER

# 追加 base64 payload（前面加标记行）
echo "" >> dist/recon_installer.sh
echo "__PAYLOAD_BELOW__" >> dist/recon_installer.sh
echo "$PAYLOAD" >> dist/recon_installer.sh

chmod +x dist/recon_installer.sh
echo "✅ 生成 dist/recon_installer.sh ($(wc -c < dist/recon_installer.sh) 字节)"
echo "   发送到目标设备后执行: bash dist/recon_installer.sh"
