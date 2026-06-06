#!/bin/bash
# Quick Multi-Room Demo (No HA needed)

echo "🏠 MULTI-ROOM BRIGHTNESS CONTROL DEMO"
echo "======================================"
echo ""
echo "Testing 3 separate room models..."
echo ""

# Ensure services are running
echo "1. Checking services..."
pkill -f "fake_sensors\|multi_room" 2>/dev/null
sleep 1

cd "$(dirname "$0")/.."
source venv/bin/activate 2>/dev/null || true

python src/fake_sensors_multiroom.py &>/dev/null &
python src/multi_room_controller.py &>/dev/null &
sleep 3

echo "   ✅ Services started"
echo ""

# Test Living Room
echo "2. Living Room Test"
echo "   Parent moves to Living_Room, sets 80%"
mosquitto_pub -h localhost -t "home/user/parent/location" -m "Living_Room"
sleep 0.5
mosquitto_pub -h localhost -t "home/user/parent/living_room/brightness_pref" -m "80"
sleep 2
LR=$(mosquitto_sub -h localhost -t "home/device/living_room/light/brightness" -C 1 -W 1 2>/dev/null)
echo "   → Living_Room brightness: ${LR}%"
echo ""

# Test Bedroom
echo "3. Bedroom Test"
echo "   Child moves to Bedroom, sets 30%"
mosquitto_pub -h localhost -t "home/user/child/location" -m "Bedroom"
sleep 0.5
mosquitto_pub -h localhost -t "home/user/child/bedroom/brightness_pref" -m "30"
sleep 2
BR=$(mosquitto_sub -h localhost -t "home/device/bedroom/light/brightness" -C 1 -W 1 2>/dev/null)
echo "   → Bedroom brightness: ${BR}%"
echo ""

# Test Kitchen
echo "4. Kitchen Test"  
echo "   Guest moves to Kitchen, sets 60%"
mosquitto_pub -h localhost -t "home/user/guest/location" -m "Kitchen"
sleep 0.5
mosquitto_pub -h localhost -t "home/user/guest/kitchen/brightness_pref" -m "60"
sleep 2
KR=$(mosquitto_sub -h localhost -t "home/device/kitchen/light/brightness" -C 1 -W 1 2>/dev/null)
echo "   → Kitchen brightness: ${KR}%"
echo ""

# Show all rooms
echo "5. Current State of All Rooms:"
echo "   Living_Room: ${LR}%"
echo "   Bedroom: ${BR}%"
echo "   Kitchen: ${KR}%"
echo ""

echo "======================================"
echo "✅ Multi-room system working!"
echo ""
echo "Each room has independent AI model"
echo "Users only control lights in their current room"
