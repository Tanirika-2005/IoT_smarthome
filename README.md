# Adaptive Smart Home System

## 📂 Project Structure

```
.
├── src/                          # Source code
│   ├── core/                     # Core AI & Controller modules
│   │   ├── multi_room_controller.py   # Main orchestrator (3 rooms)
│   │   └── brightness_learner.py      # PyTorch Neural Network engine
│   ├── rl/                       # Reinforcement Learning modules
│   │   ├── smart_home_env.py          # OpenAI Gym environment
│   │   └── train_rl_agent.py          # DQN agent training
│   └── utils/                    # Utility functions
│       ├── fake_sensors_multiroom.py  # Sensor simulation
│       └── deploy_tinyml.py           # TFLite model conversion
├── tests/                        # Test suite
│   ├── benchmark_rl.py               # RL vs baseline comparison
│   ├── test_tinyml_accuracy.py       # TFLite accuracy verification
│   ├── verify_system_integration.py  # Integration tests
│   └── trace_rl_episode.py           # Episode tracing
├── examples/                     # Example scripts & demos
│   ├── demo_continuous_learning.py   # Online learning demo
│   └── demo_multiroom.sh             # Multi-room demo script
├── home_assistant/               # Home Assistant configuration
│   ├── ha_multiroom_clean_ui.yaml    # Main HA config
│   └── ui-lovelace.yaml              # Dashboard UI
├── docs/                         # Documentation
│   ├── system_explanation.md         # Technical architecture
│   └── presentation_slides.md        # Presentation content
├── models/                       # Trained models (gitignored)
├── logs/                         # Training logs (gitignored)
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## 🧠 Core Components

### AI & Machine Learning
- **brightness_learner.py**: PyTorch-based neural network for adaptive brightness learning
- **smart_home_env.py**: OpenAI Gym environment for RL training
- **train_rl_agent.py**: Deep Q-Network (DQN) agent training

### TinyML Deployment
- **deploy_tinyml.py**: Converts PyTorch models to quantized TFLite format for edge devices (ESP32)
- **test_tinyml_accuracy.py**: Validates TFLite model accuracy

### Testing & Benchmarking
- **benchmark_rl.py**: Compares RL agent performance against random baseline
- **verify_system_integration.py**: Comprehensive system integration tests
- **trace_rl_episode.py**: Traces and analyzes individual RL episodes

### Home Assistant Integration
- **ha_multiroom_clean_ui.yaml**: MQTT sensor configuration and automation
- **ui-lovelace.yaml**: Custom Lovelace dashboard

## 🚀 Quick Start

### Installation
```bash
pip install -r requirements.txt
```

### Run Demo
```bash
cd examples
./demo_multiroom.sh
```

### Train RL Agent
```bash
python src/rl/train_rl_agent.py
```

### Deploy to Edge Device
```bash
python src/utils/deploy_tinyml.py
```

## 📊 Dependencies

- **paho-mqtt**: MQTT protocol support
- **numpy**: Numerical computing
- **scikit-learn**: Machine learning utilities
- **torch**: PyTorch deep learning
- **gymnasium**: Reinforcement learning environments
- **stable-baselines3**: RL algorithms
- **onnx**: Model format conversion
- **tensorflow-cpu**: TFLite conversion

## 📝 Configuration

Home Assistant configuration files are in `home_assistant/`:
- Update MQTT broker settings in `ha_multiroom_clean_ui.yaml`
- Customize dashboard layout in `ui-lovelace.yaml`

## 🧪 Testing

Run all tests:
```bash
pytest tests/
```

Run specific test:
```bash
python tests/benchmark_rl.py
python tests/test_tinyml_accuracy.py
python tests/verify_system_integration.py
```

## 📚 Documentation

- `docs/system_explanation.md` - Technical architecture and implementation details
- `docs/presentation_slides.md` - Presentation content and slides

## 🛠️ Development

This repository uses a clean modular structure:
- `src/` - Production code
- `tests/` - Test suites
- `examples/` - Demo scripts
- `home_assistant/` - Configuration files
- `docs/` - Documentation

