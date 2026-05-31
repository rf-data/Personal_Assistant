#!/bin/bash

set -e 

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

find ~ -type d -name "__pycache__" -exec rm -rf {} + 
find ~ -type f -name "*.pyc" -delete 
find ~ -type d -name ".pytest_cache" -exec rm -rf {} + 
find ~ -type d -name ".mypy_cache" -exec rm -rf {} +

echo "==============================" 
echo "Cleaning Jupyter..." 
echo "==============================" 

find ~ -type d -name ".ipynb_checkpoints" -exec rm -rf {} +

echo "==============================" 
echo "Cleaning logs + temp files..." 
echo "==============================" 

find ~ -type f -name "*.log" -size +50M -delete 
find /tmp -type f -atime +7 -delete 2>/dev/null || true

echo "==============================" 
echo "Cleaning user cache..." 
echo "==============================" 

rm -rf ~/.cache/thumbnails/* 
rm -rf ~/.cache/pip/* 
rm -rf ~/.cache/uv/* 
rm -rf ~/.cache/matplotlib/*

echo "==============================" 
echo "Cleaning VSCode / Cursor cache..." 
echo "==============================" 

rm -rf ~/.config/Code/Cache/* 
rm -rf ~/.config/Code/CachedData/* 
rm -rf ~/.config/Cursor/Cache/* 
rm -rf ~/.config/Cursor/CachedData/*

echo "==============================" 
echo "Cleaning HuggingFace + Torch..." 
echo "==============================" 

rm -rf ~/.cache/huggingface/* 
rm -rf ~/.cache/torch/* 
rm -rf ~/.cache/transformers/*

echo "==============================" 
echo "Cleaning npm cache..." 
echo "==============================" 

npm cache clean --force 2>/dev/null || true 


echo "==============================" 
echo "Cleaning Trash..." 
echo "==============================" 

rm -rf ~/.local/share/Trash/* 


echo "==============================" 
echo "Docker cleanup..." 
echo "==============================" 

docker system prune -af --volumes 2>/dev/null || true 

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
