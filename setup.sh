#!/bin/bash
# Setup Script for LLM Inference Web UI
# Automates installation and configuration

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Main setup
print_header "LLM Inference Web UI Setup"

# Check Node.js
print_info "Checking Node.js..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    print_success "Node.js found: $NODE_VERSION"

    # Check version
    NODE_MAJOR=$(echo $NODE_VERSION | cut -d'.' -f1 | sed 's/v//')
    if [ "$NODE_MAJOR" -lt 18 ]; then
        print_warning "Node.js version 18+ recommended (found v$NODE_MAJOR)"
    fi
else
    print_error "Node.js not found. Please install Node.js 18+ first."
    exit 1
fi

# Check Python
print_info "Checking Python..."
if command -v python &> /dev/null; then
    PYTHON_CMD=python
elif command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
else
    print_error "Python not found. Please install Python 3.9+ first."
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version)
print_success "Python found: $PYTHON_VERSION"

# Check CUDA
print_info "Checking CUDA..."
if command -v nvidia-smi &> /dev/null; then
    print_success "CUDA detected"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
else
    print_warning "CUDA not detected. CPU-only mode."
fi

# Install Node.js dependencies
print_header "Installing Node.js Dependencies"
cd webapp
print_info "Running npm install..."
npm install
print_success "Node.js dependencies installed"
cd ..

# Install Python dependencies
print_header "Installing Python Dependencies"
print_info "Installing backend requirements..."
$PYTHON_CMD -m pip install -r backend/requirements.txt
print_success "Python dependencies installed"

# Setup environment
print_header "Environment Configuration"

if [ -f "webapp/.env" ]; then
    print_warning ".env file already exists. Skipping..."
else
    print_info "Creating .env file from template..."
    cp webapp/.env.example webapp/.env
    print_success ".env file created"

    # Prompt for HF token
    echo ""
    print_info "Please configure your HuggingFace token in webapp/.env"
    print_info "Get your token from: https://huggingface.co/settings/tokens"
    echo ""
    read -p "Enter your HuggingFace token (or press Enter to skip): " HF_TOKEN

    if [ ! -z "$HF_TOKEN" ]; then
        # Update .env file
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            sed -i '' "s/HF_TOKEN=.*/HF_TOKEN=$HF_TOKEN/" webapp/.env
        else
            # Linux
            sed -i "s/HF_TOKEN=.*/HF_TOKEN=$HF_TOKEN/" webapp/.env
        fi
        print_success "HF_TOKEN configured"
    else
        print_warning "Skipped HF_TOKEN configuration. Please edit webapp/.env manually."
    fi
fi

# Verify backend can be imported
print_header "Verifying Backend"
print_info "Testing Python backend imports..."

$PYTHON_CMD -c "
import sys
sys.path.insert(0, '.')
try:
    from backend.inference_engine import InferenceEngine
    from backend.config import config
    print('✅ Backend imports successful')
except Exception as e:
    print(f'❌ Backend import error: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    print_success "Backend verification passed"
else
    print_error "Backend verification failed"
    exit 1
fi

# Create directories
print_header "Creating Directories"
print_info "Creating cache and offload directories..."
mkdir -p model_cache
mkdir -p offload
print_success "Directories created"

# Final summary
print_header "Setup Complete!"

echo ""
print_success "All dependencies installed and configured!"
echo ""

print_info "Next steps:"
echo "  1. Configure HuggingFace token (if not done):"
echo "     Edit webapp/.env and set HF_TOKEN=your_token_here"
echo ""
echo "  2. Start the server:"
echo "     cd webapp && npm start"
echo ""
echo "  3. Open your browser:"
echo "     http://localhost:3000"
echo ""

print_info "Quick start:"
echo "  cd webapp"
echo "  npm start"
echo ""

print_info "Documentation:"
echo "  • Quick Start: webapp/QUICKSTART.md"
echo "  • Full Guide: INTEGRATION_GUIDE.md"
echo "  • Overview: FINAL_OVERVIEW.md"
echo ""

print_header "Setup Script Finished"
