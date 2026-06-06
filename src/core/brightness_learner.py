import os
import torch
import torch.nn as nn
import torch.optim as optim
import csv
import time
import numpy as np
from collections import defaultdict, deque
import warnings
warnings.filterwarnings("ignore")

class BrightnessNet(nn.Module):
    def __init__(self):
        super(BrightnessNet, self).__init__()
        # Inputs: Hour (norm), Motion (0/1), Light (norm) -> 3 inputs
        self.fc1 = nn.Linear(3, 16)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(16, 8)
        self.fc3 = nn.Linear(8, 1)
        self.sigmoid = nn.Sigmoid()  # Output 0-1

    def forward(self, x):
        x = self.fc1(x)
        x = self.relu(x)
        x = self.fc2(x)
        x = self.relu(x)
        x = self.fc3(x)
        x = self.sigmoid(x)
        return x

class BrightnessLearner:
    """
    Online brightness learning using a PyTorch Neural Network.
    Learns a continuous brightness level [0,100] from context:
    [hour, motion, ambient_light].
    
    Supports multi-user conflict resolution via priority-based weighted averaging.
    """

    def __init__(self, model_file="brightness_model.pth", user_priorities=None, history_size=10, location_boost=1):
        self.model_file = model_file
        self.log_file = "brightness_training_log.csv"
        self.conflict_log_file = "conflict_resolution_log.csv"
        
        # User priority rules (higher = more important)
        self.user_priorities = user_priorities or {
            "parent": 2,
            "child": 1,
            "guest": 0,
            "default_user": 1
        }
        
        # Location-aware priority boost
        self.LOCATION_BOOST = location_boost
        self.device_location = "Living_Room"
        
        # Track per-user preference history
        self.history_size = history_size
        self.user_history = defaultdict(lambda: defaultdict(lambda: deque(maxlen=history_size)))
        
        # PyTorch Model Setup
        self.device = torch.device("cpu") # Use CPU for Raspberry Pi/Edge compatibility
        self.net = BrightnessNet().to(self.device)
        self.optimizer = optim.Adam(self.net.parameters(), lr=0.01)
        self.criterion = nn.MSELoss()
        
        self.is_trained = False
        self.sample_count = 0
        self.conflict_count = 0
        self.load_model()

    def _log_sample(self, hour, motion, light_level, target_brightness, user_id="default_user"):
        try:
            file_exists = os.path.exists(self.log_file)
            with open(self.log_file, "a", newline="") as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["hour", "motion", "light", "target_brightness", "user_id"])
                writer.writerow([hour, motion, light_level, float(target_brightness), user_id])
        except Exception as e:
            print(f"Failed to log sample: {e}")

    def _features(self, hour, motion, light_level):
        """Build feature tensor from context. Normalize to [0, 1]."""
        # Hour: 0-24 -> 0-1
        # Motion: 0 or 1
        # Light: 0-100 -> 0-1
        features = [float(hour) / 24.0, float(motion), float(light_level) / 100.0]
        return torch.tensor([features], dtype=torch.float32).to(self.device)
    
    def _context_key(self, hour, motion, light_level):
        return f"h{hour}_m{motion}_l{light_level}"
    
    def _log_conflict(self, context_key, hour, motion, light_level, user_id, user_value, resolved_value, all_prefs):
        try:
            file_exists = os.path.exists(self.conflict_log_file)
            with open(self.conflict_log_file, "a", newline="") as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["timestamp", "context", "hour", "motion", "light", "user_id", 
                                   "user_value", "resolved_value", "all_preferences", "conflict_id"])
                
                prefs_str = "; ".join([f"{uid}:{val:.1f}" for uid, val in all_prefs.items()])
                writer.writerow([
                    time.strftime("%Y-%m-%d %H:%M:%S"),
                    context_key,
                    hour,
                    motion,
                    light_level,
                    user_id,
                    user_value,
                    resolved_value,
                    prefs_str,
                    self.conflict_count
                ])
        except Exception as e:
            print(f"Failed to log conflict: {e}")
    
    def _resolve_conflict(self, context_key, hour, motion, light_level, current_user_id, current_value, user_locations=None):
        ctx_history = self.user_history[context_key]
        ctx_history[current_user_id].append((current_value, time.time()))
        
        active_users = {uid for uid, hist in ctx_history.items() if len(hist) > 0}
        
        if len(active_users) <= 1:
            return current_value, False
        
        user_prefs = {}
        for uid in active_users:
            if ctx_history[uid]:
                user_prefs[uid] = ctx_history[uid][-1][0]
        
        effective_priorities = {}
        for uid in user_prefs.keys():
            base_priority = self.user_priorities.get(uid, 0)
            user_in_room = False
            location_boost = 0
            
            if user_locations and uid in user_locations:
                user_loc = user_locations.get(uid, "Unknown")
                if user_loc == self.device_location:
                    user_in_room = True
                    location_boost = self.LOCATION_BOOST
                else:
                    continue
            else:
                user_in_room = True
            
            if user_in_room:
                effective_priorities[uid] = base_priority + location_boost
        
        if not effective_priorities:
            effective_priorities = {uid: self.user_priorities.get(uid, 0) for uid in user_prefs.keys()}
        
        max_priority = max(effective_priorities.values())
        top_users = {uid: user_prefs[uid] for uid in effective_priorities.keys() if effective_priorities[uid] == max_priority}
        
        if len(top_users) == 1:
            resolved_value = list(top_users.values())[0]
        else:
            weighted_sum = 0
            total_weight = 0
            for uid in top_users.keys():
                hist = ctx_history[uid]
                if hist:
                    for idx, (val, ts) in enumerate(hist):
                        weight = 0.8 ** (len(hist) - idx - 1)
                        weighted_sum += val * weight
                        total_weight += weight
            resolved_value = weighted_sum / total_weight if total_weight > 0 else current_value
        
        self.conflict_count += 1
        self._log_conflict(context_key, hour, motion, light_level, current_user_id, current_value, resolved_value, user_prefs)
        print(f"  ⚠️  CONFLICT #{self.conflict_count}: {len(user_prefs)} users → {user_prefs}")
        print(f"  ✓ Resolved to {resolved_value:.1f} (priority favors: {list(top_users.keys())})")
        
        return resolved_value, True

    def learn(self, hour, motion, light_level, target_brightness, user_id="default_user", user_locations=None):
        """
        Online update using Backpropagation.
        """
        context_key = self._context_key(hour, motion, light_level)
        
        # Resolve conflicts if multiple users have preferences (with location awareness)
        resolved_brightness, was_conflict = self._resolve_conflict(
            context_key, hour, motion, light_level, user_id, target_brightness, user_locations
        )
        
        # Prepare data
        X = self._features(hour, motion, light_level)
        y = torch.tensor([[float(resolved_brightness) / 100.0]], dtype=torch.float32).to(self.device) # Target 0-1
        
        # Training Step - Run multiple epochs for faster online adaptation
        self.net.train()
        for _ in range(5): # Run 5 gradient steps per interaction to learn faster
            self.optimizer.zero_grad()
            output = self.net(X)
            loss = self.criterion(output, y)
            loss.backward()
            self.optimizer.step()
        
        self.is_trained = True
        self.sample_count += 1
        
        conflict_marker = "🔥" if was_conflict else "✓"
        print(
            f"{conflict_marker} NN update #{self.sample_count}: "
            f"user={user_id}, (h={hour}, m={motion}, L={light_level}) → {resolved_brightness:.1f} | Loss: {loss.item():.4f}"
        )

        self._log_sample(hour, motion, light_level, target_brightness, user_id)

        if self.sample_count % 5 == 0:
            self.save_model()

    def predict(self, hour, motion, light_level):
        """
        Predict continuous brightness in [0,100].
        """
        if not self.is_trained:
            # Default heuristic
            if motion == 1 and light_level < 40:
                b = 60.0
            else:
                b = 0.0
            print(f"→ Default brightness: {b:.1f} (not trained yet)")
            return b

        self.net.eval()
        with torch.no_grad():
            X = self._features(hour, motion, light_level)
            pred_norm = self.net(X).item()
        
        # Denormalize
        pred = max(0.0, min(100.0, pred_norm * 100.0))
        
        print(
            f"→ NN predicted brightness: {pred:.1f} "
            f"(samples={self.sample_count})"
        )
        return pred

    def save_model(self):
        # Convert nested defaultdict to pure dict for pickling
        history_dict = {k: dict(v) for k, v in self.user_history.items()}
        
        data = {
            "model_state_dict": self.net.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "is_trained": self.is_trained,
            "sample_count": self.sample_count,
            "user_history": history_dict
        }
        
        save_path = self.model_file
        if save_path.endswith(".pkl"):
             save_path = save_path.replace(".pkl", ".pth")
        
        torch.save(data, save_path)
        print(f"💾 Neural Net model saved to {save_path}")

    def load_model(self):
        load_path = self.model_file
        if load_path.endswith(".pkl"):
             load_path = load_path.replace(".pkl", ".pth")
              
        if os.path.exists(load_path):
            try:
                checkpoint = torch.load(load_path, map_location=self.device, weights_only=False)
                self.net.load_state_dict(checkpoint["model_state_dict"])
                self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
                self.is_trained = checkpoint["is_trained"]
                self.sample_count = checkpoint["sample_count"]
                
                # Restore history (convert back to defaultdict if needed, or just load as dict)
                # For simplicity, we'll load the data into the existing defaultdict structure
                saved_history = checkpoint.get("user_history", {})
                for ctx, users in saved_history.items():
                    for uid, deque_data in users.items():
                        self.user_history[ctx][uid] = deque_data
                        
                print(f"📂 Loaded Neural Net model (samples={self.sample_count})")
            except Exception as e:
                print(f"Failed to load model: {e}")
        else:
            print("ℹ️  No existing Neural Net model found. Starting fresh.")
