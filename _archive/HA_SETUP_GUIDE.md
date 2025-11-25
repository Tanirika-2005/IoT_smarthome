# Home Assistant Setup Guide — Multi-User Brightness Demo

Quick guide to set up the visual demo for your professor.

## 🚀 Quick Setup (5 minutes)

### Step 1: Add Configuration to Home Assistant

**Option A: Via File Editor (easiest)**

1. Open Home Assistant → Settings → Add-ons → File Editor
2. Open `configuration.yaml`
3. Copy contents from `homeassistant_multiuser_config.yaml` and paste at the bottom
4. Save
5. Settings → System → Restart Home Assistant

**Option B: Via Terminal**

```bash
# Backup first
cp ~/.homeassistant/configuration.yaml ~/.homeassistant/configuration.yaml.backup

# Append our config
cat homeassistant_multiuser_config.yaml >> ~/.homeassistant/configuration.yaml

# Restart HA
# (do this from HA UI: Settings > System > Restart)
```

### Step 2: Add Dashboard

1. Go to Home Assistant Overview
2. Click the ⋮ menu (top right) → Edit Dashboard
3. Click ⋮ again → Raw Configuration Editor
4. Open `homeassistant_dashboard.yaml` and copy its contents
5. Paste and Save

### Step 3: Start Backend Services

In your terminal:

```bash
cd ~/adaptive_smart_home
source venv/bin/activate

# Terminal 1: Start multi-user sensors
python fake_sensors_multiuser.py

# Terminal 2 (new terminal): Start controller
cd ~/adaptive_smart_home
source venv/bin/activate
python smart_controller_reg.py
```

### Step 4: Demo Time! 🎉

Open the Home Assistant dashboard and show your professor:

1. **Environment panel** updates every 3 seconds (simulated hour, motion, light)
2. **User locations** show where each person is
3. **Sliders** for each user to set brightness
4. **AI gauge** shows the resolved brightness after conflict resolution
5. **Conflict status** shows recent resolution messages

---

## 🎬 Demo Script for Professor

### Scenario 1: Basic Conflict (Parent vs Child)

**Say**: "Let me show you what happens when two users want different brightness at the same time."

1. Set Parent slider to **80%**
2. Set Child slider to **20%**
3. Point to AI gauge: "See, it resolved to 80% because parent has higher priority"
4. Show terminal: "Here you can see the conflict logged: Parent priority=2, Child priority=1"

### Scenario 2: Three-Way Conflict

**Say**: "Now let's see what happens with three users all wanting different things."

1. Set Parent → **90%**
2. Set Child → **40%**
3. Set Guest → **10%**
4. Point to gauge: "Parent wins again due to highest priority"

### Scenario 3: Guest vs Child

**Say**: "Let me disable the parent preference to show child vs guest."

1. Terminal: Type `auto 1 parent` to give parent a neutral value
2. Set Child → **60%**
3. Set Guest → **20%**
4. Point to gauge: "Child wins (priority 1 > guest priority 0)"

### Scenario 4: Real-time Learning

**Say**: "The system is continuously learning from these preferences."

1. Show terminal output: Model updates after each preference
2. After a few adjustments, type `i` in controller to show model weights
3. Explain: "These weights show what the model learned about hour, motion, and light patterns"

---

## 📊 What the UI Shows

| Element | Purpose |
|---------|---------|
| **Environment Hour/Motion/Light** | Simulated sensor readings |
| **User Locations** | Where each user is in the home |
| **User Sliders** | Each user sets their brightness preference |
| **AI Gauge** | Final resolved brightness (after conflict resolution) |
| **Conflict Status** | Real-time conflict resolution messages |

---

## 🐛 Troubleshooting

### "Entities unavailable"

**Problem**: HA shows entities as "unavailable"  
**Fix**: Make sure MQTT broker is running and backend services started

```bash
# Check MQTT
sudo systemctl status mosquitto

# Restart if needed
sudo systemctl restart mosquitto
```

### "No data updating"

**Problem**: Dashboard not updating  
**Fix**: Check that backend services are running

```bash
# Should see output scrolling
cd ~/adaptive_smart_home
source venv/bin/activate
python fake_sensors_multiuser.py  # Should print sensor data every 3s
```

### "Sliders don't do anything"

**Problem**: Moving sliders doesn't trigger conflicts  
**Fix**: Make sure `smart_controller_reg.py` is running

```bash
cd ~/adaptive_smart_home
source venv/bin/activate
python smart_controller_reg.py  # Should show "Connected to MQTT broker"
```

---

## 🎯 Advanced Demo Features

### Show Conflict Logs

```bash
# During demo, open another terminal
cd ~/adaptive_smart_home
tail -f conflict_resolution_log.csv
```

Each conflict is logged with timestamp, users involved, and resolution.

### Show Model Evaluation

```bash
# After running demo for a while
pkill -f "fake_sensors"  # Stop sensors
pkill -f "smart_controller"  # Stop controller

# Evaluate collected data
python evaluate_model.py
```

This shows multi-user metrics and conflict statistics.

---

## 📸 Screenshots to Take

For your report/presentation:

1. **Dashboard overview** — All panels visible
2. **Conflict gauge** — Showing parent winning over child
3. **Terminal output** — Conflict resolution messages
4. **Evaluation results** — From `evaluate_model.py`
5. **Conflict log** — CSV showing resolution history

---

## ⏱️ Time Estimates

- **Setup**: 5 minutes (one-time)
- **Demo prep**: 30 seconds (start services)
- **Demo duration**: 2-5 minutes (scenarios 1-4)
- **Teardown**: 10 seconds (Ctrl+C the terminals)

---

## 💡 Key Talking Points for Viva

1. **"This runs entirely on edge"** — Point out it's a Raspberry Pi-class linear model
2. **"100% conflict resolution accuracy"** — Reference your evaluation results
3. **"Priority-based fairness"** — Explain parent > child > guest makes sense in homes
4. **"Continuous learning"** — Model updates in real-time from user feedback
5. **"Privacy-preserving"** — All processing local, no cloud

Good luck with your demo! 🎓
