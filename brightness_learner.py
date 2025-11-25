import os
import pickle
import csv
import time
import numpy as np
from sklearn.linear_model import SGDRegressor
from collections import defaultdict, deque
import warnings
warnings.filterwarnings("ignore")

class BrightnessLearner:
    """
    Online brightness regression for edge devices with multi-user support.
    Learns a continuous brightness level [0,100] from context:
    [hour, motion, ambient_light], using SGDRegressor + partial_fit.
    
    Supports multi-user conflict resolution via priority-based weighted averaging.
    """

    def __init__(self, model_file="brightness_model.pkl", user_priorities=None, history_size=10, location_boost=1):
        self.model_file = model_file
        self.log_file = "brightness_training_log.csv"
        self.conflict_log_file = "conflict_resolution_log.csv"
        
        # User priority rules (higher = more important)
        self.user_priorities = user_priorities or {
            "parent": 2,
            "child": 1,
            "guest": 0,
            "default_user": 1  # For backwards compatibility
        }
        
        # Location-aware priority boost
        self.LOCATION_BOOST = location_boost  # Boost for users in target room
        self.device_location = "Living_Room"  # Default device location
        
        # Track per-user preference history: context -> {user_id -> deque of (value, timestamp)}
        self.history_size = history_size
        self.user_history = defaultdict(lambda: defaultdict(lambda: deque(maxlen=history_size)))
        
        # Use Ridge regression for stable, immediate learning
        from sklearn.linear_model import Ridge
        self.model = Ridge(alpha=0.1)
        self.X_train = []
        self.y_train = []
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
        """Build feature vector from context. Normalize to [0, 1] for SGD stability."""
        return np.array([[float(hour) / 24.0, float(motion), float(light_level) / 100.0]], dtype=float)   
    
    def _context_key(self, hour, motion, light_level):
        """Create a hashable key for context (hour, motion, light)."""
        return f"h{hour}_m{motion}_l{light_level}"
    
    def _log_conflict(self, context_key, hour, motion, light_level, user_id, user_value, resolved_value, all_prefs):
        """Log conflict resolution details."""
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
        """Apply priority-based weighted averaging with location awareness to resolve conflicts.
        
        Args:
            user_locations: dict mapping user_id -> location (e.g., {"parent": "Living_Room"})
        
        Returns:
            resolved_value: The brightness value to use after conflict resolution
            was_conflict: Boolean indicating if there was actually a conflict
        """
        # Get current history for this context
        ctx_history = self.user_history[context_key]
        
        # Add current user's preference
        ctx_history[current_user_id].append((current_value, time.time()))
        
        # Check if there's a conflict (multiple users with recent preferences)
        active_users = {uid for uid, hist in ctx_history.items() if len(hist) > 0}
        
        if len(active_users) <= 1:
            # No conflict, single user
            return current_value, False
        
        # CONFLICT DETECTED
        # Get most recent preference from each user
        user_prefs = {}
        for uid in active_users:
            if ctx_history[uid]:
                # Get most recent value
                user_prefs[uid] = ctx_history[uid][-1][0]  # (value, timestamp)
        
        # Calculate effective priority with location boost
        # IMPORTANT: Only consider users who are IN the device's room!
        effective_priorities = {}
        for uid in user_prefs.keys():
            base_priority = self.user_priorities.get(uid, 0)
            
            # Check if user is in the device's room
            user_in_room = False
            location_boost = 0
            
            if user_locations and uid in user_locations:
                user_loc = user_locations.get(uid, "Unknown")
                if user_loc == self.device_location:
                    user_in_room = True
                    location_boost = self.LOCATION_BOOST
                    print(f"  📍 {uid} in {self.device_location} → +{self.LOCATION_BOOST} priority boost")
                else:
                    # User NOT in room - skip them (don't control this room's light!)
                    print(f"  🚫 {uid} in {user_loc}, not in {self.device_location} → IGNORED")
                    continue
            else:
                # No location data - include user by default (backward compatible)
                user_in_room = True
            
            # Only add to effective priorities if user is in room
            if user_in_room:
                effective_priorities[uid] = base_priority + location_boost
        
        # If NO users are in the room, use all preferences (fallback)
        if not effective_priorities:
            print(f"  ℹ️  No users in {self.device_location}, using all preferences")
            effective_priorities = {
                uid: self.user_priorities.get(uid, 0) 
                for uid in user_prefs.keys()
            }
        
        # Find max effective priority among active users (in room)
        max_priority = max(effective_priorities.values())
        
        # Filter to highest-priority users (after location filtering and boost)
        top_users = {
            uid: user_prefs[uid] for uid in effective_priorities.keys()
            if effective_priorities[uid] == max_priority
        }
        
        # Among equal-priority users, use recency-weighted average
        if len(top_users) == 1:
            resolved_value = list(top_users.values())[0]
        else:
            # Weighted average: more recent = higher weight
            weighted_sum = 0
            total_weight = 0
            for uid in top_users.keys():
                hist = ctx_history[uid]
                if hist:
                    # Weight by recency (exponential decay)
                    for idx, (val, ts) in enumerate(hist):
                        weight = 0.8 ** (len(hist) - idx - 1)  # More recent = higher weight
                        weighted_sum += val * weight
                        total_weight += weight
            
            resolved_value = weighted_sum / total_weight if total_weight > 0 else current_value
        
        # Log the conflict
        self.conflict_count += 1
        self._log_conflict(context_key, hour, motion, light_level, current_user_id, 
                          current_value, resolved_value, user_prefs)
        
        # Print conflict resolution message
        print(f"  ⚠️  CONFLICT #{self.conflict_count}: {len(user_prefs)} users → {user_prefs}")
        print(f"  ✓ Resolved to {resolved_value:.1f} (priority favors: {list(top_users.keys())})")
        
        return resolved_value, True

    def learn(self, hour, motion, light_level, target_brightness, user_id="default_user", user_locations=None):
        """
        Online update from a single labeled sample with multi-user support.
        target_brightness in [0,100].
        user_id: identifier for the user providing this preference (default: "default_user")
        user_locations: dict mapping user_id -> location for location-aware conflict resolution
        """
        context_key = self._context_key(hour, motion, light_level)
        
        # Resolve conflicts if multiple users have preferences (with location awareness)
        resolved_brightness, was_conflict = self._resolve_conflict(
            context_key, hour, motion, light_level, user_id, target_brightness, user_locations
        )
        
        # Train model with resolved value
        # Normalize target to [0, 1] for stability
        X = self._features(hour, motion, light_level)
        y_val = float(resolved_brightness) / 100.0
        
        # Accumulate training data
        self.X_train.append(X[0])
        self.y_train.append(y_val)
        
        # Refit model with all data
        if len(self.X_train) > 0:
            self.model.fit(np.array(self.X_train), np.array(self.y_train))
            self.is_trained = True
        
        self.sample_count += 1
        
        conflict_marker = "🔥" if was_conflict else "✓"
        print(
            f"{conflict_marker} REG update #{self.sample_count}: "
            f"user={user_id}, (h={hour}, m={motion}, L={light_level}) → {resolved_brightness:.1f}"
        )

        self._log_sample(hour, motion, light_level, target_brightness, user_id)

        if self.sample_count % 5 == 0:
            self.save_model()

    def predict(self, hour, motion, light_level):
        """
        Predict continuous brightness in [0,100].
        If not trained, fall back to a simple heuristic.
        """
        if not self.is_trained:
            # Default: if dark + motion → 60%, else 0
            if motion == 1 and light_level < 40:
                b = 60.0
            else:
                b = 0.0
            print(f"→ Default brightness: {b:.1f} (not trained yet)")
            return b

        X = self._features(hour, motion, light_level)
        # Predict in [0, 1] range
        pred_norm = float(self.model.predict(X)[0])
        
        # Denormalize to [0, 100] and clamp
        pred = max(0.0, min(100.0, pred_norm * 100.0))
        
        print(
            f"→ REG predicted brightness: {pred:.1f} "
            f"(samples={self.sample_count})"
        )
        return pred

    def get_model_info(self):
        if not self.is_trained:
            return None
        try:
            coef = self.model.coef_
            intercept = float(self.model.intercept_[0])
            return {
                "weights": {
                    "hour": float(coef[0]),
                    "motion": float(coef[1]),
                    "light": float(coef[2]),
                    "intercept": intercept,
                },
                "samples": int(self.sample_count),
            }
        except Exception:
            return None

    def save_model(self):
        data = {
            "model": self.model,
            "is_trained": self.is_trained,
            "sample_count": self.sample_count,
        }
        with open(self.model_file, "wb") as f:
            pickle.dump(data, f)
        print("💾 Regression model saved.")

    def load_model(self):
        if os.path.exists(self.model_file):
            try:
                with open(self.model_file, "rb") as f:
                    data = pickle.load(f)
                self.model = data["model"]
                self.is_trained = bool(data["is_trained"])
                self.sample_count = int(data["sample_count"])
                print(
                    f"📂 Loaded brightness model "
                    f"(samples={self.sample_count})."
                )
            except Exception as e:
                print(f"Failed to load brightness model: {e}")

learner = BrightnessLearner()
