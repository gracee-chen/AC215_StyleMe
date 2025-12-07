#!/bin/bash
# NVIDIA Driver Installation Script

echo "🚀 Installing NVIDIA GPU Driver"
echo "======================"

# 1. Install necessary tools
echo "📦 Step 1: Installing necessary tools..."
sudo apt-get update
sudo apt-get install -y wget software-properties-common

# 2. Disable built-in drivers
echo "📦 Step 2: Disabling drivers that may cause conflicts..."
sudo bash -c 'cat > /etc/modprobe.d/blacklist-nouveau.conf << EOF
blacklist nouveau
options nouveau modeset=0
EOF'

# 3. Add NVIDIA official PPA (Debian 11)
echo "📦 Step 3: Adding NVIDIA repository..."
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)

# 4. Download and install NVIDIA driver
echo "📦 Step 4: Installing NVIDIA driver..."
sudo apt-get install -y \
    linux-headers-$(uname -r) \
    build-essential

# 5. Prompt user to restart
echo ""
echo "✅ NVIDIA driver installation script ready"
echo "================================="
echo ""
echo "⚠️  Important Notes:"
echo "   1. Server restart required after installation"
echo "   2. After restart, run: nvidia-smi to verify"
echo "   3. Run training only after successful verification"
echo ""
echo "Proceed with installation now? (Server restart required)"
read -p "Continue installation? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "📦 Starting GPU driver installation (this may take some time)..."
    sudo apt-get install -y nvidia-driver-470
    echo ""
    echo "✅ Driver installation complete! Server restart required"
    echo "   Run: sudo reboot"
else
    echo "Installation cancelled"
fi

