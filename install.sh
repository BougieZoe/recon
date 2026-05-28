#!/bin/bash
# RECON 安装脚本 — macOS / Linux / Termux
set -e

REPO="https://github.com/YOUR_USER/recon.git"
INSTALL_DIR="$HOME/.recon"
BIN_DIR="$HOME/.local/bin"

detect_platform() {
  case "$(uname -s)" in
    Darwin) echo "macos" ;;
    Linux)
      if [ -f /data/data/com.termux/files/usr/bin/bash ]; then
        echo "termux"
      else
        echo "linux"
      fi ;;
    *) echo "unknown" ;;
  esac
}

install_deps() {
  local plat=$1
  case "$plat" in
    macos)
      if ! command -v brew &>/dev/null; then
        echo "请先安装 Homebrew: https://brew.sh"
        exit 1
      fi
      brew install openssl bind whois python3
      ;;
    termux)
      pkg update -y
      pkg install -y python openssl-tool dnsutils whois curl
      BIN_DIR="$HOME/bin"
      mkdir -p "$BIN_DIR"
      ;;
    linux)
      echo "请手动安装: python3, openssl, dnsutils (dig), whois"
      ;;
  esac
}

setup() {
  local plat=$1
  mkdir -p "$INSTALL_DIR"

  if [ ! -f "$INSTALL_DIR/recon.py" ]; then
    if command -v git &>/dev/null; then
      git clone "$REPO" /tmp/recon_install
      cp -r /tmp/recon_install/* "$INSTALL_DIR/"
      rm -rf /tmp/recon_install
    else
      echo "请先安装 git 或手动复制文件到 $INSTALL_DIR"
      exit 1
    fi
  fi

  mkdir -p "$BIN_DIR"
  cat > "$BIN_DIR/recon" << 'BIN'
#!/usr/bin/env bash
PYTHONPATH="$HOME/.recon" exec python3 "$HOME/.recon/recon.py" "$@"
BIN
  chmod +x "$BIN_DIR/recon"

  echo "✅ RECON 已安装"
  echo "   运行: recon example.com"
  echo "   如果 $BIN_DIR 不在 PATH 中："
  echo "   echo 'export PATH=\"$BIN_DIR:\$PATH\"' >> ~/.bashrc && source ~/.bashrc"
}

PLATFORM=$(detect_platform)
echo "📦 平台: $PLATFORM"
install_deps "$PLATFORM"
setup "$PLATFORM"
