# Adaptive Smart Home System

## 📂 Project Structure

### 🧠 Core AI & Controller
- **`src/multi_room_controller.py`**: The main brain. Orchestrates 3 rooms (Living Room, Bedroom, Kitchen).
- **`src/brightness_learner.py`**: The AI Engine. Uses PyTorch Neural Networks for continuous learning.
- **`src/fake_sensors_multiroom.py`**: Simulates motion, light, and time sensors for testing.

### 🚀 Reinforcement Learning & TinyML
- **`src/smart_home_env.py`**: Custom OpenAI Gym environment for RL.
- **`src/train_rl_agent.py`**: Trains the Deep Q-Network (DQN) agent.
- **`src/deploy_tinyml.py`**: Converts the PyTorch model to a quantized TFLite model for ESP32.

### 📊 Benchmarks & Tests
- **`src/benchmark_rl.py`**: Compares RL agent against a random baseline.
- **`src/test_tinyml_accuracy.py`**: Verifies TFLite model accuracy vs PyTorch.
- **`src/verify_system_integration.py`**: Full system integration test suite.
- **`src/demo_continuous_learning.py`**: Proof-of-concept for online learning.

### 🏠 Home Assistant
- **`config/ha_multiroom_clean_ui.yaml`**: Main configuration (MQTT sensors, sliders).
- **`config/ui-lovelace.yaml`**: Custom Dashboard configuration.

### 🏃‍♂️ Run the Demo
```bash
./scripts/demo_multiroom.sh
```

### 📚 Documentation
- **`docs/system_explanation.md`**: Detailed technical architecture.
- **`docs/presentation_slides.md`**: Content for presentation.
