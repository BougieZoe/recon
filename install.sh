#!/bin/bash
# Detects OS and sets up recon accordingly
# Supports: macOS, Linux, Termux (Android)

# Clone if not exists
if [ ! -d ~/.recon ]; then
  git clone https://github.com/BougieZoe/recon.git ~/.recon
fi

# Install Python deps
cd ~/.recon
pip3 install -r requirements.txt --break-system-packages 2>/dev/null || \
pip3 install -r requirements.txt

# Add alias based on shell
ALIAS_LINE="alias recon='python3 ~/.recon/recon.py --person --theme green'"

for RC in ~/.zshrc ~/.bashrc ~/.bash_profile; do
  if [ -f "$RC" ]; then
    grep -q "alias recon=" "$RC" || echo "$ALIAS_LINE" >> "$RC"
  fi
done

# Termux special case
if [ -d "/data/data/com.termux" ]; then
  grep -q "alias recon=" ~/.bashrc || echo "$ALIAS_LINE" >> ~/.bashrc
fi

echo "✓ recon installed — restart terminal or run: source ~/.zshrc"
echo "  then just type: recon"
