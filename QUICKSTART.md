# Quick Start Guide - Home Assistant Demo

## 📁 Files Overview

### For HA Demo (Use these):
- **`smart_controller_ha.py`** ← NEW! Headless controller for HA
- **`fake_sensors_multiuser.py`** ← Simulates environment
- **`homeassistant_dashboard_simple.yaml`** ← Dashboard config
- **`demo_check.sh`** ← Verify everything is working

### For Benchmarking/Testing (Keep original):
- **`smart_controller_reg.py`** ← Original with terminal commands
- **`evaluate_model.py`** ← Evaluation metrics
- **`policy_trainer_multiuser.py`** ← Generate test data
- **`generate_test_data.py`** ← Quick data generation

---

## 🚀 Start Demo (2 Steps)

### Step 1: Start Backend Services
```bash
cd ~/adaptive_smart_home && source venv/bin/activate

# Terminal 1: Sensors
python fake_sensors_multiuser.py &

# Terminal 2: HA Controller (headless)
python smart_controller_ha.py &
```

### Step 2: Test It Works
```bash
./demo_check.sh
```

Move a slider during the 8-second wait. You should see:
```
✅ HA sliders → MQTT working!
home/user/parent/brightness_pref 80.0
✅ AI publishing brightness: 80%
```

---

## 🎯 Demo Flow

1. **Open HA** → Your dashboard
2. **Move Parent slider** to 80%
3. **Move Child slider** to 30%
4. **Watch AI Output gauge** → Shows 80% (parent wins!)
5. **Explain**: "Parent has priority 2, child has priority 1, so parent's preference is used for training the model and setting the output"

---

## 📊 For Benchmarks (Use Original Controller)

```bash
# Stop HA controller first
pkill -f smart_controller_ha

# Start original for testing
python smart_controller_reg.py

# Interactive terminal commands:
# 'b 80 parent' → Train parent preference
# 'auto 50' → Auto-generate 50 samples
# 'i' → Show model info
```

Then run evaluation:
```bash
python evaluate_model.py
```

---

## 🔍 Verify Live Flow

Watch realtime logs:
```bash
# Watch HA controller processing
tail -f /tmp/controller_ha.log

# Watch MQTT messages
mosquitto_sub -h localhost -t "home/#" -v

# Check what gauge is showing
mosquitto_sub -h localhost -t "home/device/light/brightness" -C 1
```

---

## Key Differences

| Feature | smart_controller_ha.py | smart_controller_reg.py |
|---------|------------------------|-------------------------|
| Purpose | HA Demo | Testing/Benchmarks |
| Input | MQTT only | Terminal + MQTT |
| Interactive | No (headless) | Yes (commands) |
| Best for | Live demos | Data generation, evaluation |
