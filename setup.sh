#!/bin/bash
set -e

# Project root (directory containing this script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Setting up Serial Killer 2.0"
if [ -d ".venv" ]; then
    echo "Virtual environment already exists"
else
    echo "Creating virtual environment"
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install -r requirements.txt

# Paths for the desktop file
VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"
INSTALL_DESKTOP="/usr/share/applications/SK.desktop"
TEMP_DESKTOP="$SCRIPT_DIR/SK.desktop.install"

# Generate SK.desktop with correct paths
echo "Creating desktop entry with paths:"
echo "  Python: $VENV_PYTHON"
echo "  Project: $SCRIPT_DIR"
cat > "$TEMP_DESKTOP" << EOF
[Desktop Entry]
Version=1.0
Name=Serial-Killer2
Comment=Serial Interface program
Exec=$VENV_PYTHON $SCRIPT_DIR/SK.py -x 800 -y 800
Path=$SCRIPT_DIR
Icon=$SCRIPT_DIR/img/SK_Icon.png
Terminal=True
Type=Application
StartupWMClass=python3
EOF

# Install to /usr/share/applications/ (requires sudo)
if [ -f "$INSTALL_DESKTOP" ]; then
    echo ""
    read -p "SK.desktop already exists at $INSTALL_DESKTOP. Overwrite? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Skipping desktop file install. You can install it later with: sudo cp $TEMP_DESKTOP $INSTALL_DESKTOP && sudo chmod 644 $INSTALL_DESKTOP"
        rm -f "$TEMP_DESKTOP"
        echo "Serial Killer 2.0 setup complete"
        exit 0
    fi
fi

echo "Installing desktop file to $INSTALL_DESKTOP (sudo required)"
sudo cp "$TEMP_DESKTOP" "$INSTALL_DESKTOP"
sudo chmod 644 "$INSTALL_DESKTOP"
rm -f "$TEMP_DESKTOP"

# Ensure user is in dialout group (required for serial port access)
if ! groups | grep -qw dialout; then
    echo "Adding you to the dialout group (required for serial port access)..."
    sudo usermod -aG dialout "$USER"
    echo ""
    echo "You have been added to the dialout group. Please restart your computer for the changes to take effect."
    echo ""
fi

echo "Serial Killer 2.0 setup complete"