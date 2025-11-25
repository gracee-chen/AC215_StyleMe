#!/bin/bash
# NVIDIA 驱动安装脚本

echo "🚀 安装 NVIDIA GPU 驱动"
echo "======================"

# 1. 安装必要的工具
echo "📦 步骤 1: 安装必要的工具..."
sudo apt-get update
sudo apt-get install -y wget software-properties-common

# 2. 禁用自带驱动
echo "📦 步骤 2: 禁用可能导致冲突的驱动..."
sudo bash -c 'cat > /etc/modprobe.d/blacklist-nouveau.conf << EOF
blacklist nouveau
options nouveau modeset=0
EOF'

# 3. 添加 NVIDIA 官方 PPA (Debian 11)
echo "📦 步骤 3: 添加 NVIDIA 仓库..."
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)

# 4. 下载并安装 NVIDIA 驱动
echo "📦 步骤 4: 安装 NVIDIA 驱动..."
sudo apt-get install -y \
    linux-headers-$(uname -r) \
    build-essential

# 5. 提示用户需要重启
echo ""
echo "✅ NVIDIA 驱动安装脚本准备完成"
echo "================================="
echo ""
echo "⚠️  重要提示："
echo "   1. 安装完成后需要重启服务器"
echo "   2. 重启后运行: nvidia-smi 验证"
echo "   3. 验证成功后再运行训练"
echo ""
echo "现在运行安装吗？(需要重启服务器)"
read -p "继续安装? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "📦 开始安装 GPU 驱动 (这需要一些时间)..."
    sudo apt-get install -y nvidia-driver-470
    echo ""
    echo "✅ 驱动安装完成！现在需要重启服务器"
    echo "   运行: sudo reboot"
else
    echo "安装已取消"
fi

