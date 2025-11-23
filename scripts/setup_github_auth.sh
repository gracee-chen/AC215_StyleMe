#!/bin/bash
# Setup GitHub authentication for cloning private repositories

echo "=========================================="
echo "GitHub Authentication Setup"
echo "=========================================="
echo ""

# Check if SSH key exists
if [ -f ~/.ssh/id_rsa ] || [ -f ~/.ssh/id_ed25519 ]; then
    echo "✅ SSH key found"
    if [ -f ~/.ssh/id_ed25519.pub ]; then
        echo "Your public SSH key (id_ed25519):"
        cat ~/.ssh/id_ed25519.pub
    elif [ -f ~/.ssh/id_rsa.pub ]; then
        echo "Your public SSH key (id_rsa):"
        cat ~/.ssh/id_rsa.pub
    fi
    echo ""
    echo "To use SSH:"
    echo "1. Copy the public key above"
    echo "2. Go to https://github.com/settings/keys"
    echo "3. Click 'New SSH key' and paste it"
    echo ""
else
    echo "⚠️  No SSH key found"
    echo ""
    echo "To generate an SSH key:"
    echo "  ssh-keygen -t ed25519 -C \"your_email@example.com\""
    echo "  eval \"\$(ssh-agent -s)\""
    echo "  ssh-add ~/.ssh/id_ed25519"
    echo ""
fi

# Check for GitHub CLI
if command -v gh &> /dev/null; then
    echo "✅ GitHub CLI (gh) is installed"
    echo ""
    echo "To authenticate:"
    echo "  gh auth login"
    echo ""
    echo "Then try cloning again:"
    echo "  gh repo clone gracee-chen/AC215_StyleMe /tmp/ac215_clone"
else
    echo "⚠️  GitHub CLI not installed"
    echo ""
    echo "To install GitHub CLI:"
    echo "  # On Ubuntu/Debian:"
    echo "  curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg"
    echo "  echo \"deb [arch=\$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main\" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null"
    echo "  sudo apt update && sudo apt install gh"
    echo ""
fi

echo "=========================================="
echo "Alternative: Use Personal Access Token"
echo "=========================================="
echo ""
echo "1. Go to: https://github.com/settings/tokens"
echo "2. Generate new token (classic) with 'repo' scope"
echo "3. Clone using:"
echo "   git clone https://<token>@github.com/gracee-chen/AC215_StyleMe.git /tmp/ac215_clone"
echo ""

