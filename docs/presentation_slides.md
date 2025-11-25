# Adaptive Smart Home - Presentation Slides

## Slide 1: Title Slide
**Title:** Adaptive Smart Home System
**Subtitle:** Privacy-First AI with Reinforcement Learning & Edge Computing
**Presenter:** Tanirika
**Date:** November 2025

---

## Slide 2: The Problem
*   **Static Automation:** Traditional smart homes rely on rigid schedules (e.g., "Turn lights on at 6 PM").
*   **Privacy Concerns:** Most AI assistants send voice/video data to the cloud.
*   **Energy Waste:** Lights stay on when not needed, or are too bright for the context.
*   **User Conflict:** "I want it bright, she wants it dark" - who wins?

---

## Slide 3: The Solution
An **Adaptive, Privacy-First System** that learns your preferences in real-time.
*   **Local AI:** All processing happens on-device (no cloud).
*   **Context-Aware:** Learns from Time, Motion, and Ambient Light.
*   **Energy Efficient:** Optimizes brightness to save power without sacrificing comfort.

---

## Slide 4: System Architecture
*   **Controller:** Python-based orchestration engine.
*   **Communication:** MQTT (Message Queuing Telemetry Transport) for decoupled, real-time messaging.
*   **User Interface:** Home Assistant (Custom YAML Dashboard).
*   **AI Engine:** PyTorch Neural Network running locally.

---

## Slide 5: Key Innovation 1 - Reinforcement Learning
*   **Algorithm:** Deep Q-Network (DQN).
*   **Goal:** Balance **Energy Savings** vs. **User Comfort**.
*   **How it works:**
    *   The AI gets a "Reward" for saving energy.
    *   It gets a "Penalty" if you manually override it (signaling discomfort).
    *   **Result:** 40% Energy reduction compared to static baselines.

---

## Slide 6: Key Innovation 2 - TinyML on Edge
*   **Challenge:** Running Neural Networks on cheap microcontrollers (ESP32).
*   **Pipeline:** PyTorch Training → ONNX Export → TFLite Conversion → **Quantization**.
*   **Result:**
    *   Model Size: **2.82 KB** (Compressed from 500KB+).
    *   Accuracy: **98.4%** retention of original performance.
    *   Latency: < 10ms inference time.

---

## Slide 7: Key Innovation 3 - Multi-User Conflict Resolution
*   **Scenario:** Parent (Priority 2) and Child (Priority 1) are in the same room.
*   **Logic:**
    1.  **Location Awareness:** System knows who is in which room.
    2.  **Priority Boosting:** Higher priority user wins.
    3.  **Recency Weighting:** If priorities are equal, the most recent command has more weight.
*   **Outcome:** Seamless, argument-free lighting control.

---

## Slide 8: Live Demo Results
*   **Continuous Learning:** Demonstrated the model adapting to a new preference (60% → 85%) in just **5 interactions**.
*   **Integration:** Full bi-directional control via Home Assistant.
*   **Stability:** Verified with extensive integration tests.

---

## Slide 9: Future Roadmap
*   **Voice Control:** Local LLM (Llama 3.2) for natural language commands.
*   **Presence Detection:** mmWave sensors for precise localization.
*   **Energy Grid:** Integrate with solar panels to optimize for peak/off-peak rates.

---

## Slide 10: Q&A
**Thank You!**
*   Code Repository: GitHub/Tanirika-2005/IoT_smarthome
