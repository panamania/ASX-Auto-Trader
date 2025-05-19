#!/bin/bash

echo "Installing ASX Trader as a system service..."

# Get the current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

# Copy service file
sudo cp "$SCRIPT_DIR/asx-trader.service" /etc/systemd/system/
echo "Service file installed."

# Update paths in service file
sudo sed -i "s|/home/ubuntu/apps/ASX-Auto-Trader|$PROJECT_DIR|g" /etc/systemd/system/asx-trader.service
sudo sed -i "s|User=ubuntu|User=$(whoami)|g" /etc/systemd/system/asx-trader.service
echo "Service file paths updated."

# Copy logrotate configuration
sudo cp "$SCRIPT_DIR/asx-trader.logrotate" /etc/logrotate.d/asx-trader
echo "Log rotation configuration installed."

# Update paths in logrotate configuration
sudo sed -i "s|/home/ubuntu/apps/ASX-Auto-Trader|$PROJECT_DIR|g" /etc/logrotate.d/asx-trader
sudo sed -i "s|ubuntu ubuntu|$(whoami) $(whoami)|g" /etc/logrotate.d/asx-trader
echo "Log rotation configuration paths updated."

# Copy management script to user's home directory
cp "$SCRIPT_DIR/manage-asx-trader.sh" ~/manage-asx-trader.sh
chmod +x ~/manage-asx-trader.sh
echo "Management script installed to your home directory."

# Create data directory if it doesn't exist
mkdir -p "$PROJECT_DIR/data"

# Reload systemd
sudo systemctl daemon-reload
echo "Systemd configuration reloaded."

echo "Installation complete!"
echo ""
echo "To enable and start the service, run:"
echo "  sudo systemctl enable asx-trader"
echo "  sudo systemctl start asx-trader"
echo ""
echo "To manage the service, use the management script:"
echo "  ~/manage-asx-trader.sh [start|stop|restart|status|logs|update|backup]"
