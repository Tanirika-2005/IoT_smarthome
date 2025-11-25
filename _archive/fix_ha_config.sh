#!/bin/bash
# Fix duplicate sliders in Home Assistant

echo "🔧 Fixing Home Assistant configuration..."

# Backup current config
echo "1. Backing up current configuration..."
sudo cp /home/tanirika/homeassistant/configuration.yaml /home/tanirika/homeassistant/configuration.yaml.old

# Find where our multiuser config starts and remove it
echo "2. Removing old multi-user config..."
sudo sed -i '/# Multi-User Brightness Control/,$ d' /home/tanirika/homeassistant/configuration.yaml

# Add clean config
echo "3. Adding clean configuration (no duplicates)..."
sudo sh -c "cat /home/tanirika/adaptive_smart_home/homeassistant_config_clean.yaml >> /home/tanirika/homeassistant/configuration.yaml"

# Show what was added
echo ""
echo "✅ Configuration updated!"
echo ""
echo "Added:"
tail -20 /home/tanirika/homeassistant/configuration.yaml
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 NEXT STEP:"
echo "Go to Home Assistant → Profile → Restart Home Assistant"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
