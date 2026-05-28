#!/data/data/com.termux/files/usr/bin/bash
# RECON Termux 一键安装
set -e

echo "🔍 RECON 安装中..."

# 安装依赖
pkg update -y
pkg install -y python openssl-tool dnsutils whois curl

# 克隆 / 复制
mkdir -p ~/.recon
cd ~/.recon

# 如果从 GitHub 拉取
if [ ! -f recon.py ]; then
  if command -v git &>/dev/null; then
    git clone https://github.com/YOUR_USER/recon.git /tmp/recon_src
    cp -r /tmp/recon_src/* ~/.recon/
    rm -rf /tmp/recon_src
  else
    pkg install -y git
    git clone https://github.com/YOUR_USER/recon.git /tmp/recon_src
    cp -r /tmp/recon_src/* ~/.recon/
    rm -rf /tmp/recon_src
  fi
fi

# 建立 PATH 链接
mkdir -p ~/bin
cat > ~/bin/recon << 'BIN'
#!/data/data/com.termux/files/usr/bin/bash
PYTHONPATH="$HOME/.recon" exec python3 "$HOME/.recon/recon.py" "$@"
BIN
chmod +x ~/bin/recon

echo "✅ 完成！现在输入 'recon example.com' 即可使用"
echo "   如果 ~/bin 不在 PATH 中，请执行: echo 'export PATH=\$HOME/bin:\$PATH' >> ~/.bashrc && source ~/.bashrc"
