#!/usr/bin/env python3
"""
Quick test data generator for multi-user conflict resolution.
Generates synthetic multi-user brightness preferences without needing MQTT.
"""

import csv
import random

# Per-user brightness policies
def get_brightness_preference(user_id, hour, motion, light_level):
    if motion == 0:
        return 0.0
    
    if user_id == "parent":
        if light_level < 20:
            return 80.0
        elif 20 <= light_level < 60:
            return 70.0
        else:
            return 40.0
    elif user_id == "child":
        if light_level < 20:
            return 60.0
        elif 20 <= light_level < 60:
            return 50.0
        else:
            return 30.0
    elif user_id == "guest":
        if light_level < 20:
            return 70.0
        elif 20 <= light_level < 60:
            return 60.0
        else:
            return 35.0
    
    return 50.0

# Generate test data
def generate_multiuser_dataset(n_samples=150):
    """Generate multi-user conflict scenarios."""
    data = []
    
    for _ in range(n_samples):
        # Random context
        hour = random.randint(0, 23)
        motion = random.choice([0, 1])
        light = random.randint(0, 100)
        
        active_users = []
        
        # Parent active most of the day
        if 6 <= hour < 22:
            active_users.append("parent")
        
        # Child active during day/evening
        if 7 <= hour < 21 and random.random() < 0.7:
            active_users.append("child")
        
        # Guest occasionally  
        if 9 <= hour < 18 and random.random() < 0.3:
            active_users.append("guest")
        
        # Add preferences for each active user
        if active_users:
            for user_id in active_users:
                brightness = get_brightness_preference(user_id, hour, motion, light)
                data.append({
                    "hour": hour,
                    "motion": motion,
                    "light": light,
                    "target_brightness": brightness,
                    "user_id": user_id
                })
    
    return data

if __name__ == "__main__":
    print("Generating multi-user test dataset...")
    data = generate_multiuser_dataset(150)
    
    # Write to CSV
    with open("brightness_training_log.csv", "w", newline="") as f:
        fieldnames = ["hour", "motion", "light", "target_brightness", "user_id"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    print(f"Generated {len(data)} samples")
    
    # Count conflicts (same context, multiple users)
    contexts = {}
    for row in data:
        key = (row["hour"], row["motion"], row["light"])
        if key not in contexts:
            contexts[key] = set()
        contexts[key].add(row["user_id"])
    
    conflicts = sum(1 for users in contexts.values() if len(users) > 1)
    print(f"Potential conflict contexts: {conflicts}")
    
    # User distribution
    user_counts = {}
    for row in data:
        uid = row["user_id"]
        user_counts[uid] = user_counts.get(uid, 0) + 1
    
    print("\nPer-user samples:")
    for uid, count in sorted(user_counts.items()):
        print(f"  {uid}: {count}")
