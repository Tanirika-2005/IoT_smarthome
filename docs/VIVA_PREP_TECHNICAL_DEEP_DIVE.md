# Viva Preparation: Technical Deep Dive

This document provides a line-by-line technical explanation of the core Machine Learning and AI components. Use this to answer "Why?" and "How?" questions during your viva.

---

## 1. The Neural Network (`brightness_learner.py`)

### **Class: `BrightnessNet`**
This is the "Brain" of the system. It is a **Multi-Layer Perceptron (MLP)**.

```python
class BrightnessNet(nn.Module):
    def __init__(self):
        super(BrightnessNet, self).__init__()
        # Layer 1: Input -> Hidden
        self.fc1 = nn.Linear(3, 64)  
        # Layer 2: Hidden -> Hidden
        self.fc2 = nn.Linear(64, 32)
        # Layer 3: Hidden -> Output
        self.output = nn.Linear(32, 1) 
```

**Viva Explanation:**
*   **Why 3 Inputs?** The inputs are `[Hour, Motion, Ambient_Light]`. These are the 3 critical context features needed to decide brightness.
*   **Why 64 & 32 Neurons?** This is the "Capacity" of the model.
    *   If too small (e.g., 5 neurons), it can't learn complex patterns (Underfitting).
    *   If too large (e.g., 1000 neurons), it's too slow for the ESP32 and might memorize data (Overfitting).
    *   64/32 is a balanced architecture for this specific complexity.
*   **Why `nn.Linear`?** These are "Fully Connected" layers. Every input is connected to every neuron, allowing the model to combine features (e.g., "Late night" + "Motion" = "Lights On").

### **Forward Pass**
```python
def forward(self, x):
    x = torch.relu(self.fc1(x))  # Activation Function
    x = torch.relu(self.fc2(x))
    x = torch.sigmoid(self.output(x)) # Output Activation
    return x
```

**Viva Explanation:**
*   **ReLU (Rectified Linear Unit):** `f(x) = max(0, x)`.
    *   *Why?* It introduces **Non-Linearity**. Without it, the whole network would just be one big linear regression equation. ReLU allows it to learn "If-Then" type logic.
*   **Sigmoid:** `f(x) = 1 / (1 + e^-x)`.
    *   *Why?* It squashes the output to be strictly between **0 and 1**. Since brightness is a percentage (0-100%), this ensures the model never predicts -50% or 200%.

---

## 2. Online Learning (`learn` method)

This is how the model adapts in real-time.

```python
def learn(self, ...):
    # 1. Loss Function
    self.criterion = nn.MSELoss() 
    
    # 2. Optimizer
    self.optimizer = optim.Adam(self.net.parameters(), lr=0.01)

    # 3. Backpropagation Loop
    self.net.train()
    for _ in range(5): # Epochs
        self.optimizer.zero_grad()   # Clear previous gradients
        output = self.net(X)         # Forward pass
        loss = self.criterion(output, y) # Calculate error
        loss.backward()              # Calculate gradients (Backprop)
        self.optimizer.step()        # Update weights
```

**Viva Explanation:**
*   **MSE Loss (Mean Squared Error):** Measures the average squared difference between the *Predicted Brightness* and the *User's Desired Brightness*. We want to minimize this to 0.
*   **Adam Optimizer:** An advanced gradient descent algorithm.
    *   *Why?* It adapts the learning rate for each parameter individually. It converges much faster than standard SGD (Stochastic Gradient Descent).
*   **Why 5 Epochs?** Since we are learning from a *single* interaction (batch size = 1), running just one update might not be enough to "nudge" the weights significantly. Running 5 updates helps the model learn the new preference faster without forgetting everything else (Catastrophic Forgetting).

---

## 3. Reinforcement Learning Environment (`smart_home_env.py`)

This is the simulation world for the DQN agent.

### **Observation Space**
```python
self.observation_space = spaces.Box(
    low=np.array([0, 0, 0, 0, 0]), 
    high=np.array([24, 1, 100, 100, np.inf]), ...
)
```
**Viva Explanation:**
The agent sees 5 things: `[Hour, Motion, Ambient Light, Current Brightness, Accumulated Energy]`. This is the "State" $S$.

### **Action Space**
```python
self.action_space = spaces.Discrete(5)
# 0: -10%, 1: -5%, 2: Hold, 3: +5%, 4: +10%
```
**Viva Explanation:**
Instead of setting an absolute value (e.g., "Set to 60%"), the agent makes *relative* adjustments. This is smoother and more natural for a control system.

### **The Reward Function (The Most Important Part)**
```python
energy_cost = (new_brightness / 100.0) * 0.1 
comfort_penalty = abs(new_brightness - ideal_brightness) * 0.05
reward = -energy_cost - comfort_penalty
```

**Viva Explanation:**
*   **Goal:** Maximize Reward (which means minimizing the negative penalty).
*   **Component 1: Energy Cost.** The higher the brightness, the bigger the penalty. This pushes the agent to turn lights **OFF**.
*   **Component 2: Comfort Penalty.** The further the brightness is from the user's "Ideal" (simulated), the bigger the penalty. This pushes the agent to turn lights **ON**.
*   **Result:** The agent finds the **Equilibrium**—the lowest possible brightness that satisfies the user.

---

## 4. TinyML Pipeline (`deploy_tinyml.py`)

This is how we fit the AI onto a chip.

### **Step 1: ONNX Export**
```python
torch.onnx.export(model, dummy_input, "model.onnx", ...)
```
**Viva Explanation:**
ONNX (Open Neural Network Exchange) is a universal format. It allows us to move the model out of Python/PyTorch and into a generic representation that other tools (like TensorFlow) can understand.

### **Step 2: Quantization (Int8)**
```python
converter.optimizations = [tf.lite.Optimize.DEFAULT]
```
**Viva Explanation:**
*   **Float32 (Original):** Every weight is a 32-bit decimal number (e.g., `0.12345678`). Takes 4 bytes.
*   **Int8 (Quantized):** We map these decimals to integers between -128 and 127. Takes 1 byte.
*   **Result:**
    *   Size: Reduced by **4x**.
    *   Speed: Integer math is much faster for CPUs than floating-point math.
    *   Accuracy: We lose a tiny bit of precision (rounding errors), but our tests showed < 2% loss.
