#!/bin/bash
# Complete test of Home Assistant → MQTT → Controller flow

echo "🧪 Testing Multi-User Brightness Control Flow"
echo "=============================================="
echo ""

echo "Step 1: Check MQTT broker..."
if pgrep mosquitto > /dev/null; then
    echo "✅ MQTT broker running"
else
    echo "❌ MQTT broker not running"
    exit 1
fi

echo ""
echo "Step 2: Subscribe to user preference topics..."
echo "   (Move a slider in HA within the next 10 seconds)"
echo ""

timeout 10 mosquitto_sub -h localhost -t "home/user/+/brightness_pref" -v -C 1 &
SUB_PID=$!

sleep 11
if kill -0 $SUB_PID 2>/dev/null; then
   kill $SUB_PID
    echo "❌ No MQTT messages received from HA sliders"
    echo "   → Automations may not be active"
else
    echo "✅ Received MQTT message from HA slider!"
fi

echo ""
echo "Step 3: Check if controller is receiving messages..."
if tail -5 /tmp/controller.log | grep -q "REG update"; then
    echo "✅ Controller is processing updates"
    tail -3 /tmp/controller.log
else
    echo "⚠️  Controller log doesn't show recent updates"
    echo "   Last few lines:"
    tail -3 /tmp/controller.log
fi

echo ""
echo "Step 4: Check AI output is being published..."
timeout 5 mosquitto_sub -h localhost -t "home/device/light/brightness" -C 1 -v

echo ""
echo "=============================================="
echo "Test complete. Check results above."
