#!/bin/bash
# HiveRecon Tool Installation Script
# Installs all required security scanning tools

set -e

echo "🐝 HiveRecon Tool Installer"
echo "=========================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${YELLOW}Note: Some tools require sudo. You may be prompted for password.${NC}"
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install nmap (if broken or missing)
echo -e "\n${GREEN}[1/5]${NC} Checking nmap..."
if command_exists nmap; then
    if nmap --version >/dev/null 2>&1; then
        echo "✓ nmap is working"
    else
        echo "⚠ nmap is installed but broken (library issue)"
        echo "  Fixing lua library symlink..."
        ln -sf /usr/lib/liblua.so.5.4.8 /usr/lib/liblua5.4.so.5.4 2>/dev/null || sudo ln -sf /usr/lib/liblua.so.5.4.8 /usr/lib/liblua5.4.so.5.4
        if nmap --version >/dev/null 2>&1; then
            echo "✓ nmap fixed!"
        else
            echo -e "${RED}✗ Could not fix nmap. Try: sudo pacman -S nmap${NC}"
        fi
    fi
else
    echo "Installing nmap..."
    pacman -S --noconfirm nmap || sudo pacman -S nmap
fi

# Install Go tools (subfinder, katana, nuclei)
echo -e "\n${GREEN}[2/5]${NC} Checking Go installation..."
if command_exists go; then
    GO_VERSION=$(go version)
    echo "✓ $GO_VERSION"
else
    echo -e "${YELLOW}⚠ Go is not installed. Install with: sudo pacman -S go${NC}"
fi

# Install subfinder
echo -e "\n${GREEN}[3/5]${NC} Checking subfinder..."
if command_exists subfinder; then
    echo "✓ subfinder is installed"
else
    if command_exists go; then
        echo "Installing subfinder..."
        go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
        export PATH=$PATH:$(go env GOPATH)/bin
        echo "✓ subfinder installed!"
    else
        echo -e "${YELLOW}⚠ Skipping subfinder (Go not available)${NC}"
    fi
fi

# Install katana
echo -e "\n${GREEN}[4/5]${NC} Checking katana..."
if command_exists katana; then
    echo "✓ katana is installed"
else
    if command_exists go; then
        echo "Installing katana..."
        go install -v github.com/projectdiscovery/katana/cmd/katana@latest
        export PATH=$PATH:$(go env GOPATH)/bin
        echo "✓ katana installed!"
    else
        echo -e "${YELLOW}⚠ Skipping katana (Go not available)${NC}"
    fi
fi

# Install nuclei
echo -e "\n${GREEN}[5/5]${NC} Checking nuclei..."
if command_exists nuclei; then
    echo "✓ nuclei is installed"
else
    if command_exists go; then
        echo "Installing nuclei..."
        go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
        export PATH=$PATH:$(go env GOPATH)/bin
        echo "✓ nuclei installed!"
    else
        echo -e "${YELLOW}⚠ Skipping nuclei (Go not available)${NC}"
    fi
fi

# Add Go bin to PATH in bashrc
echo -e "\n${GREEN}Updating PATH...${NC}"
if ! grep -q "GOPATH/bin" ~/.bashrc 2>/dev/null; then
    echo 'export PATH="$PATH:$(go env GOPATH)/bin"' >> ~/.bashrc
    echo "✓ Added Go bin to PATH in ~/.bashrc"
fi

echo ""
echo "=========================="
echo -e "${GREEN}Installation Complete!${NC}"
echo ""
echo "To start using HiveRecon:"
echo "  source ~/.bashrc"
echo "  cd /home/vibhxr/hiverecon"
echo "  source venv/bin/activate"
echo "  python -m hiverecon scan -t example.com"
echo ""
echo "Or use the desktop shortcut: Search for 'HiveRecon Scanner' in applications"
