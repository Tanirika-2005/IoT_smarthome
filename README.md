# Adaptive Smart Home System

## 📂 Project Structure

### 🧠 Core AI & Controller
- **`multi_room_controller.py`**: The main brain. Orchestrates 3 rooms (Living Room, Bedroom, Kitchen).
- **`brightness_learner.py`**: The AI Engine. Uses PyTorch Neural Networks for continuous learning.
- **`fake_sensors_multiroom.py`**: Simulates motion, light, and time sensors for testing.

### 🚀 Reinforcement Learning & TinyML
- **`smart_home_env.py`**: Custom OpenAI Gym environment for RL.
- **`train_rl_agent.py`**: Trains the Deep Q-Network (DQN) agent.
- **`deploy_tinyml.py`**: Converts the PyTorch model to a quantized TFLite model for ESP32.

### 📊 Benchmarks & Tests
- **`benchmark_rl.py`**: Compares RL agent against a random baseline.
- **`test_tinyml_accuracy.py`**: Verifies TFLite model accuracy vs PyTorch.
- **`verify_system_integration.py`**: Full system integration test suite.
- **`demo_continuous_learning.py`**: Proof-of-concept for online learning.

### 🏠 Home Assistant
- **`ha_multiroom_clean_ui.yaml`**: Main configuration (MQTT sensors, sliders).
- **`ui-lovelace.yaml`**: Custom Dashboard configuration.

### 🏃‍♂️ Run the Demo
```bash
./demo_multiroom.sh
```

### 📚 Documentation
- **`docs/system_explanation.md`**: Detailed technical architecture.
- **`docs/presentation_slides.md`**: Content for presentation.
