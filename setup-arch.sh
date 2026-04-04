#!/bin/bash
# HiveRecon Setup Script for Arch Linux

set -e

echo "🐝 HiveRecon Setup Script (Arch Linux)"
echo "======================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() { echo -e "${GREEN}✓${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }
print_info() { echo -e "${YELLOW}→${NC} $1"; }

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Do NOT run as root! Use sudo inside the script when needed."
    exit 1
fi

# Install system dependencies
install_system_deps() {
    print_info "Installing system dependencies..."
    
    # Update package database
    sudo pacman -Sy --noconfirm
    
    # Install Python and pip
    sudo pacman -S --noconfirm python python-pip python-virtualenv
    
    # Install other dependencies (skip lua54 conflict by installing lua first)
    # nmap depends on lua, so we install lua explicitly to avoid conflicts
    sudo pacman -S --noconfirm lua
    
    # Now install remaining packages, skip lua54 if it conflicts
    sudo pacman -S --noconfirm nmap git go docker docker-compose || {
        print_info "Some packages had conflicts, trying without docker-compose..."
        sudo pacman -S --noconfirm nmap git go docker
    }
    
    print_status "System dependencies installed"
}

# Setup Python virtual environment
setup_venv() {
    print_info "Setting up Python virtual environment..."
    
    if [ ! -d "venv" ]; then
        python -m venv venv
        print_status "Virtual environment created"
    fi
    
    # Activate venv
    source venv/bin/activate
    print_status "Virtual environment activated"
}

# Install Python dependencies
install_python_deps() {
    print_info "Installing Python dependencies..."
    
    # Upgrade pip first
    pip install --upgrade pip
    
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_status "Python dependencies installed"
    fi
}

# Setup Groq API key
setup_groq() {
    print_info "Setting up Groq API key..."

    if [ -f "config/.env" ]; then
        if grep -q "GROQ_API_KEY" config/.env; then
            print_status "GROQ_API_KEY already configured in config/.env"
        else
            print_info "Add your GROQ_API_KEY to config/.env:"
            print_info "  GROQ_API_KEY=gsk_your_key_here"
        fi
    else
        print_info "Create config/.env and add:"
        print_info "  GROQ_API_KEY=gsk_your_key_here"
    fi

    print_status "Groq AI configured (get a free key at https://console.groq.com)"
}

# Install recon tools via Go
install_recon_tools() {
    print_info "Installing reconnaissance tools..."
    
    # Set Go environment
    export GOPATH=$HOME/go
    export PATH=$PATH:$GOPATH/bin
    
    # Install subfinder
    if ! command -v subfinder &> /dev/null; then
        print_info "Installing subfinder..."
        go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
        print_status "subfinder installed"
    else
        print_status "subfinder already installed"
    fi
    
    # Install nuclei
    if ! command -v nuclei &> /dev/null; then
        print_info "Installing nuclei..."
        go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
        print_status "nuclei installed"
    else
        print_status "nuclei already installed"
    fi
    
    # Install katana
    if ! command -v katana &> /dev/null; then
        print_info "Installing katana..."
        go install -v github.com/projectdiscovery/katana/cmd/katana@latest
        print_status "katana installed"
    else
        print_status "katana already installed"
    fi
    
    # Install ffuf
    if ! command -v ffuf &> /dev/null; then
        print_info "Installing ffuf..."
        go install -v github.com/joohoi/ffuf@latest
        print_status "ffuf installed"
    else
        print_status "ffuf already installed"
    fi
    
    # nmap is installed via pacman above
    print_status "nmap installed"
    
    print_status "All recon tools installed"
}

# Setup configuration
setup_config() {
    print_info "Setting up configuration..."
    
    mkdir -p config data/reports data/logs data/audit
    
    if [ ! -f "config/.env" ] && [ -f "config/.env.example" ]; then
        cp config/.env.example config/.env
        print_status "Configuration file created"
    fi
    
    # Initialize database
    print_info "Initializing database..."
    source venv/bin/activate
    python -c "from hiverecon.database import init_db; from hiverecon.config import get_config; import asyncio; asyncio.run(init_db(get_config().get_database_url()))"
    print_status "Database initialized"
}

# Enable Docker service
setup_docker() {
    print_info "Setting up Docker..."
    
    # Enable and start Docker service
    sudo systemctl enable --now docker
    
    # Add user to docker group (requires logout/login)
    if ! groups | grep -q docker; then
        sudo usermod -aG docker $USER
        print_info "Added user to docker group (logout/login required)"
    fi
    
    print_status "Docker configured"
}

# Show next steps
show_next_steps() {
    echo ""
    echo "=========================================="
    echo "🐝 HiveRecon Setup Complete!"
    echo "=========================================="
    echo ""
    echo "Next steps:"
    echo ""
    echo "1. Activate virtual environment:"
    echo "   source venv/bin/activate"
    echo ""
    echo "2. Run a scan with CLI:"
    echo "   python -m hiverecon scan -t example.com"
    echo ""
    echo "3. Or start the API server:"
    echo "   python -m hiverecon.api.server"
    echo ""
    echo "4. Or use Docker:"
    echo "   docker-compose up -d"
    echo ""
    echo "⚠️  Remember: Only scan targets you have authorization to test!"
    echo ""
}

# Main
main() {
    install_system_deps
    echo ""
    
    setup_venv
    echo ""
    
    install_python_deps
    echo ""

    setup_groq
    echo ""

    install_recon_tools
    echo ""
    
    setup_config
    echo ""
    
    setup_docker
    echo ""
    
    show_next_steps
}

main "$@"
