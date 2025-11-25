#!/bin/bash
# Quick verification script for professor demo

echo "🎯 DEMO READINESS CHECK"
echo "======================="
echo ""

echo "1️⃣  Checking backend services..."
if pgrep -f "fake_sensors_multiuser" > /dev/null; then
    echo "  ✅ Sensor simulator running"
else
    echo "  ❌ Sensor simulator NOT running"
    echo "     Run: cd ~/adaptive_smart_home && source venv/bin/activate && python fake_sensors_multiuser.py &"
fi

if pgrep -f "smart_controller_reg" > /dev/null; then
    echo "  ✅ Controller running"  
else
    echo "  ❌ Controller NOT running"
    echo "     Run: cd ~/adaptive_smart_home && source venv/bin/activate && python smart_controller_reg.py &"
fi

if pgrep mosquitto > /dev/null; then
    echo "  ✅ MQTT broker running"
else
    echo "  ❌ MQTT broker NOT running"
fi

if docker ps | grep -q homeassistant; then
    echo "  ✅ Home Assistant running"
else
    echo "  ❌ Home Assistant NOT running"
fi

echo ""
echo "2️⃣  Testing MQTT flow (move a slider NOW!)..."
echo "     Waiting 8 seconds for slider input..."
timeout 8 mosquitto_sub -h localhost -t "home/user/+/brightness_pref" -C 1 -v

if [ $? -eq 0 ]; then
    echo "  ✅ HA sliders → MQTT working!"
else
    echo "  ⚠️  No MQTT message detected (did you move a slider?)"
fi

echo ""
echo "3️⃣  Checking if AI is publishing results..."
LAST_AI=$(mosquitto_sub -h localhost -t "home/device/light/brightness" -C 1 -W 2 2>/dev/null)
if [ -n "$LAST_AI" ]; then
    echo "  ✅ AI publishing brightness: $LAST_AI%"
else
    echo "  ⚠️  No AI output detected"
fi

echo ""
echo "======================="
echo "Demo ready? Check ✅ marks above"
