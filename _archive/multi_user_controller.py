import time
import json
from collections import defaultdict, deque
from typing import Dict, List, Tuple, Optional

class MultiUserController:
    def __init__(self, priority_rules: Dict[str, int], history_size: int = 10):
        """
        Args:
            priority_rules: {"user_id": priority_level} (higher = more important)
            history_size: Number of recent entries to keep per context
        """
        self.priority_rules = priority_rules
        self.history_size = history_size
        self.history = defaultdict(deque)  # context -> deque of (value, timestamp, user_id)
        self.conflict_log = "conflict_log.txt"
        
        # Initialize log file
        with open(self.conflict_log, "a") as f:
            f.write("\n=== New Session ===\n")

    def update(self, context: str, new_value: float, user_id: str) -> float:
        """Update brightness for a context and resolve conflicts.
        
        Args:
            context: String like "hour=12,motion=1,light=30"
            new_value: Brightness value (0-100)
            user_id: ID of the user providing the input
            
        Returns:
            Resolved brightness value after applying priority rules
        """
        # Get current history for this context
        history = self.history[context]
        
        # Add new entry
        entry = (new_value, time.time(), user_id)
        history.append(entry)
        
        # Trim old entries
        while len(history) > self.history_size:
            history.popleft()
            
        # Resolve conflicts
        resolved_value = self._resolve_conflict(context, user_id)
        return resolved_value
    
    def _resolve_conflict(self, context: str, current_user: str) -> float:
        """Apply priority rules and weighted averaging."""
        history = self.history[context]
        if not history:
            return 50.0  # Default
        
        # Get max priority level in history
        max_priority = max(
            self.priority_rules.get(uid, 0) 
            for _, _, uid in history
        )
        
        # Filter to highest-priority users only
        top_entries = [
            (v, t, uid) for v, t, uid in history
            if self.priority_rules.get(uid, 0) == max_priority
        ]
        
        # Calculate weights (newer = higher weight)
        weights = [0.9 ** (len(top_entries) - i - 1) for i in range(len(top_entries))]
        total_weight = sum(weights)
        if total_weight > 0:
            weights = [w / total_weight for w in weights]  # Normalize
        
        # Weighted average
        resolved_value = sum(v * w for (v, _, _), w in zip(top_entries, weights))
        
        # Log if there was a conflict (multiple users)
        users_in_history = {uid for _, _, uid in history}
        if len(users_in_history) > 1:
            self._log_conflict(context, current_user, resolved_value, top_entries)
            
        return resolved_value
    
    def _log_conflict(self, context: str, current_user: str, 
                     resolved_value: float, top_entries: List[Tuple[float, float, str]]):
        """Log conflicts to a file for analysis."""
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "context": context,
            "current_user": current_user,
            "resolved_value": resolved_value,
            "top_entries": [
                {"value": v, "user": uid, "time": time.strftime("%H:%M:%S", time.localtime(t))}
                for v, t, uid in top_entries
            ]
        }
        
        with open(self.conflict_log, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    
    def get_history(self, context: str) -> List[Tuple[float, float, str]]:
        """Get history for a specific context."""
        return list(self.history.get(context, []))

# Example usage
if __name__ == "__main__":
    # Define user priorities (higher = more important)
    priority_rules = {
        "parent": 2,
        "child": 1,
        "guest": 0
    }
    
    controller = MultiUserController(priority_rules)
    
    # Simulate updates
    context = "hour=12,motion=1,light=30"
    print(controller.update(context, 80, "parent"))  # Parent sets to 80
    print(controller.update(context, 20, "child"))   # Child tries to set to 20 (parent's value stays)
    print(controller.update(context, 90, "parent"))  # Parent overrides to 90
    print(controller.update(context, 30, "guest"))   # Guest has lowest priority (ignored)