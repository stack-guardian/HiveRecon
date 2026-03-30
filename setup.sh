#!/bin/bash
# HiveRecon Setup Script
# Automates installation and configuration

set -e

echo "🐝 HiveRecon Setup Script"
echo "========================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${YELLOW}Warning: Running as root. Consider using a regular user account.${NC}"
fi

# Function to print status
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}→${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."
    
    # Check Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_status "Python 3 found: $PYTHON_VERSION"
    else
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    
    # Check pip
    if command -v pip3 &> /dev/null; then
        print_status "pip3 found"
    else
        print_error "pip3 is required but not installed"
        exit 1
    fi
    
    # Check Docker (optional)
    if command -v docker &> /dev/null; then
        print_status "Docker found (optional)"
    else
        print_info "Docker not found - some features will be unavailable"
    fi
    
    # Check Go (for building tools)
    if command -v go &> /dev/null; then
        print_status "Go found (for building recon tools)"
    else
        print_info "Go not found - will use pre-built tools or Docker"
    fi
}

# Install Python dependencies
install_python_deps() {
    print_info "Installing Python dependencies..."
    
    if [ -f "requirements.txt" ]; then
        pip3 install -r requirements.txt
        print_status "Python dependencies installed"
    else
        print_error "requirements.txt not found"
        exit 1
    fi
}

# Install Ollama
install_ollama() {
    print_info "Checking Ollama installation..."
    
    if command -v ollama &> /dev/null; then
        print_status "Ollama already installed"
        ollama serve &
    else
        print_info "Installing Ollama..."
        curl -fsSL https://ollama.com/install.sh | sh
        print_status "Ollama installed"
        
        # Start Ollama service
        print_info "Starting Ollama service..."
        ollama serve &
        sleep 5
    fi
    
    # Pull recommended model
    print_info "Pulling AI model (qwen2.5:7b)..."
    ollama pull qwen2.5:7b
    print_status "AI model ready"
}

# Install recon tools
install_recon_tools() {
    print_info "Installing reconnaissance tools..."
    
    # Check if Go is available
    if ! command -v go &> /dev/null; then
        print_info "Go not found - skipping tool installation"
        print_info "Tools will be available when using Docker"
        return
    fi
    
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
    
    # Install nmap (system package)
    if ! command -v nmap &> /dev/null; then
        print_info "Installing nmap..."
        if [ -x "$(command -v apt)" ]; then
            sudo apt-get install -y nmap
        elif [ -x "$(command -v yum)" ]; then
            sudo yum install -y nmap
        elif [ -x "$(command -v brew)" ]; then
            brew install nmap
        else
            print_error "Could not install nmap automatically"
        fi
    else
        print_status "nmap already installed"
    fi
    
    print_status "Recon tools installation complete"
}

# Setup configuration
setup_config() {
    print_info "Setting up configuration..."
    
    # Create config directory
    mkdir -p config data/reports data/logs data/audit
    
    # Copy environment file
    if [ ! -f "config/.env" ] && [ -f "config/.env.example" ]; then
        cp config/.env.example config/.env
        print_status "Configuration file created: config/.env"
    fi
    
    # Create database
    print_info "Initializing database..."
    python3 -c "from hiverecon.database import init_db; from hiverecon.config import get_config; import asyncio; asyncio.run(init_db(get_config().get_database_url()))"
    print_status "Database initialized"
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
    echo "1. Start Ollama (if not running):"
    echo "   ollama serve"
    echo ""
    echo "2. Run a scan with CLI:"
    echo "   python3 -m hiverecon scan -t example.com"
    echo ""
    echo "3. Or start the API server:"
    echo "   python3 -m hiverecon.api.server"
    echo ""
    echo "4. Access the dashboard:"
    echo "   cd dashboard && npm install && npm start"
    echo ""
    echo "5. Or use Docker:"
    echo "   docker-compose up -d"
    echo ""
    echo "⚠️  Remember: Only scan targets you have authorization to test!"
    echo ""
}

# Main installation
main() {
    check_prerequisites
    echo ""
    
    install_python_deps
    echo ""
    
    install_ollama
    echo ""
    
    install_recon_tools
    echo ""
    
    setup_config
    echo ""
    
    show_next_steps
}

# Run installation
main "$@"
