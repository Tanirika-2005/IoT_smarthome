#!/bin/bash
# Quick start for demo - handles model training automatically

cd ~/adaptive_smart_home
source venv/bin/activate

echo "🚀 Starting Adaptive Smart Home System..."
echo ""

# Check if model needs training
if [ ! -f "brightness_model.pkl" ]; then
    echo "📊 First time setup: Generating training data..."
    python generate_test_data.py > /dev/null
    echo "   ✅ Model trained with 180+ samples"
else
    echo "✅ Using existing trained model"
fi

echo ""
echo "🔧 Starting services..."

# Kill any existing processes
pkill -f "fake_sensors_multiuser\|smart_controller_ha" 2>/dev/null

# Start services
python fake_sensors_multiuser.py &>/dev/null &
SENSOR_PID=$!
echo "   ✅ Sensor simulator (PID: $SENSOR_PID)"

sleep 1

python smart_controller_ha.py &>/dev/null &
CONTROLLER_PID=$!
echo "   ✅ HA controller (PID: $CONTROLLER_PID)"

sleep 2

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ System Ready!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Open Home Assistant: http://localhost:8123"
echo ""
echo "Features enabled:"
echo "  • Multi-user conflict resolution"
echo "  • Location-aware priority boosting"
echo "  • Real-time edge learning"
echo ""
echo "To stop: pkill -f 'fake_sensors\|smart_controller'"
