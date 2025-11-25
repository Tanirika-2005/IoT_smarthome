#!/bin/bash
# Auto-setup script for Home Assistant Multi-User Config

echo "🔧 Setting up Home Assistant configuration..."

# Backup
echo "1. Backing up configuration.yaml..."
sudo cp /home/tanirika/homeassistant/configuration.yaml /home/tanirika/homeassistant/configuration.yaml.backup

# Add config
echo "2. Adding multi-user configuration..."
sudo sh -c "cat /home/tanirika/adaptive_smart_home/homeassistant_multiuser_config.yaml >> /home/tanirika/homeassistant/configuration.yaml"

# Verify
echo "3. Verifying configuration..."
tail -10 /home/tanirika/homeassistant/configuration.yaml

echo ""
echo "✅ Configuration added successfully!"
echo ""
echo "📋 NEXT STEPS:"
echo "1. Go to Home Assistant UI"
echo "2. Click your profile (bottom left) → 'Restart Home Assistant'"
echo "3. Wait 30 seconds for restart"
echo "4. Then run: ./create_dashboard.sh"
echo ""
