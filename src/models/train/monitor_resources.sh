#!/bin/bash
# Resource monitoring script for training
# Run this in a separate terminal while training

echo "🔍 Monitoring System Resources..."
echo "Press Ctrl+C to stop"
echo ""

while true; do
    clear
    echo "=== System Resources Monitor ==="
    echo ""
    
    # Memory
    echo "📊 Memory:"
    free -h | grep -E "Mem|Swap"
    echo ""
    
    # CPU
    echo "💻 CPU:"
    top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print "CPU Usage: " 100 - $1 "%"}'
    echo ""
    
    # GPU (if available)
    if command -v nvidia-smi &> /dev/null; then
        echo "🎮 GPU:"
        nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits | \
        awk -F', ' '{printf "  %s: %d/%d MB (%.1f%%), GPU Util: %s%%\n", $1, $2, $3, ($2/$3)*100, $4}'
        echo ""
    fi
    
    # Disk I/O
    echo "💾 Disk I/O:"
    iostat -x 1 1 2>/dev/null | tail -n +4 || echo "  (iostat not available)"
    echo ""
    
    # Process info
    echo "🔧 Top Processes (by CPU):"
    ps aux --sort=-%cpu | head -6 | tail -5
    echo ""
    
    echo "Last updated: $(date '+%Y-%m-%d %H:%M:%S')"
    sleep 2
done

