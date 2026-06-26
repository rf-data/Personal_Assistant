#!/bin/bash

set -e 

PROJECTS="$HOME/0_Portfolio_Projekte"

EXCLUDES=(
  "$HOME/0_Portfolio_Projekte/gmp_compliance/monitoring"
)

echo "==============================" 
echo "Cleaning package manager..." 
echo "=============================="

echo "Cleaning APT…"
sudo apt-get clean
sudo apt-get autoremove -y
sudo journalctl --vacuum-size=200M

echo "==============================" 
echo "Cleaning Python caches..." 
echo "==============================" 

pip cache purge || true 
uv cache clean || true

# find ~ -type d -name "__pycache__" -exec rm -rf {} + 
find "$PROJECTS" \
  -path "${EXCLUDES[0]}" -prune -o \
  -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$PROJECTS" \
  -path "${EXCLUDES[0]}" -prune -o \
  -type f -name "*.pyc" -exec rm -f {} +
find "$PROJECTS" \
  -path "${EXCLUDES[0]}" -prune -o \
  -type d -name ".pytest_cache" -exec rm -rf {} + 
find "$PROJECTS" \
  -path "${EXCLUDES[0]}" -prune -o \
  -type d -name ".mypy_cache" -exec rm -rf {} +

echo ""
echo "==============================" 
echo "Cleaning Jupyter..." 
echo "==============================" 

find "$PROJECTS" \
  -path "${EXCLUDES[0]}" -prune -o \
  -type d -name ".ipynb_checkpoints" -exec rm -rf {} +

echo ""
echo "==============================" 
echo "Cleaning logs + temp files..." 
echo "==============================" 

find "$PROJECTS" \
  -path "${EXCLUDES[0]}" -prune -o \
  -type f -name "*.log" -size +50M -exec rm -f {} +
find /tmp -type f -atime +7 -delete 2>/dev/null || true

echo ""
echo "==============================" 
echo "Cleaning user cache..." 
echo "==============================" 

rm -rf ~/.cache/thumbnails/* 
rm -rf ~/.cache/pip/* 
rm -rf ~/.cache/uv/* 
rm -rf ~/.cache/matplotlib/*

echo ""
echo "==============================" 
echo "Cleaning VSCode / Cursor cache..." 
echo "==============================" 

rm -rf ~/.config/Code/Cache/* 
rm -rf ~/.config/Code/CachedData/* 
rm -rf ~/.config/Cursor/Cache/* 
rm -rf ~/.config/Cursor/CachedData/*

echo ""
echo "==============================" 
echo "Cleaning HuggingFace + Torch..." 
echo "==============================" 

rm -rf ~/.cache/huggingface/* 
rm -rf ~/.cache/torch/* 
rm -rf ~/.cache/transformers/*

echo ""
echo "==============================" 
echo "Cleaning npm cache..." 
echo "==============================" 

npm cache clean --force 2>/dev/null || true 


echo ""
echo "==============================" 
echo "Cleaning Trash..." 
echo "==============================" 

rm -rf ~/.local/share/Trash/* 

echo ""
echo "==============================" 
echo "Docker cleanup..." 
echo "==============================" 

# docker system prune -af || true 
# --volumes 2>/dev/null  
docker container prune
docker image prune

echo ""
echo "===== DOCKER VOLUMES ====="
docker volume ls

echo ""
echo "==============================" 
echo "Disk usage summary" 
echo "==============================" 

echo "home level"
du -sh ~/* 2>/dev/null | sort -hr | head -10 

echo ""
echo "in 0_Portfolio_Projekte"
du -sh ~/0_Portfolio_Projekte/* 2>/dev/null | sort -hr | head -20 

# echo "" 
# echo "Cleanup complete."

# sudo apt autoremove --purge
# sudo apt clean

# echo "Cleaning pip + uv cache…"
# pip cache purge
# uv cache clean   

# echo home caches
# rm -rf ~/.cache/*


# echo "Cleaning Jupyter checkpoints…"
# find ~ -type d -name ".ipynb_checkpoints" -exec rm -rf {} +

# echo "Cleaning large logs and temp files…"
# find ~ -type f -name "*.log" -size +50M -delete


# # 

# echo "Cleanup complete."
