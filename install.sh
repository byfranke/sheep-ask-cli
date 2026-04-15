#!/bin/bash
# Sheep Ask CLI Quick Installation Script
# Copyright (c) 2026 byFranke - Security Solutions

echo "================================="
echo "  Sheep Ask CLI Installation"
echo "================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is required but not installed"
    echo "Please install Python 3.7 or higher"
    exit 1
fi

echo "[OK] Python 3 found"

# Install pip if needed
if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
    echo "Installing pip..."
    python3 -m ensurepip --default-pip 2>/dev/null || {
        echo "[ERROR] pip is not installed and could not be installed automatically"
        echo "Please install pip manually"
        exit 1
    }
fi

echo "[OK] pip found"

# Install requirements
echo ""
echo "Installing dependencies..."

echo "Trying: pip3 install --user..."
if pip3 install -r requirements.txt --user 2>&1 | grep -q "Successfully installed"; then
    echo "[OK] Dependencies installed with pip3 --user"
else
    if pip3 install -r requirements.txt --user 2>&1 | grep -q "externally-managed-environment"; then
        echo ""
        echo "System uses externally managed Python (PEP 668)."
        echo "Trying: pip3 install --break-system-packages..."

        if pip3 install -r requirements.txt --break-system-packages; then
            echo "[OK] Dependencies installed with --break-system-packages"
        else
            echo "[ERROR] Failed to install dependencies"
            echo ""
            echo "Please try one of these options manually:"
            echo ""
            echo "Option 1: Force install (may affect system):"
            echo "  sudo pip3 install -r requirements.txt --break-system-packages"
            echo ""
            echo "Option 2: Use a virtual environment (recommended):"
            echo "  python3 -m venv venv"
            echo "  source venv/bin/activate"
            echo "  pip install -r requirements.txt"
            echo ""
            echo "Option 3: Use system packages:"
            echo "  sudo apt install python3-rich python3-cryptography python3-keyring python3-git"
            echo ""
            exit 1
        fi
    else
        echo "[ERROR] Failed to install dependencies"
        echo "Try: pip3 install -r requirements.txt"
        exit 1
    fi
fi

echo "[OK] Dependencies installed"

# Make executable
chmod +x sheep-ask-cli.py setup.py

echo ""
echo "================================="
echo "  Installation Complete!"
echo "================================="
echo ""
echo "Next steps:"
echo "1. Configure your API token:"
echo "   python3 setup.py"
echo ""
echo "2. Test the installation:"
echo "   ./sheep-ask-cli.py --version"
echo ""
echo "For help: ./sheep-ask-cli.py --help"
