#!/usr/bin/env python3
"""
Pre-trains the room models using the generated test data.
Ensures the live system starts with smart predictions (not 0/100).
"""
import csv
import os
from brightness_learner import BrightnessLearner

def pretrain():
    print("🚀 Pre-training models from brightness_training_log.csv...")
    
    # 1. Load Data
    data = []
    if not os.path.exists("brightness_training_log.csv"):
        print("❌ No training data found! Run generate_test_data.py first.")
        return

    with open("brightness_training_log.csv", "r") as f:
        reader = csv.DictReader(f)
        data = list(reader)
    
    print(f"📊 Loaded {len(data)} samples.")

    # 2. Initialize Learners for each room
    rooms = {
        "living_room": BrightnessLearner(model_file="models/living_room_model.pkl"),
        "bedroom": BrightnessLearner(model_file="models/bedroom_model.pkl"),
        "kitchen": BrightnessLearner(model_file="models/kitchen_model.pkl")
    }
    
    # 3. Train each room with the FULL dataset
    # (In a real home, rooms would have different data, but for demo 
    #  we want all rooms to be smart immediately)
    
    count = 0
    for row in data:
        try:
            hour = int(row["hour"])
            motion = int(row["motion"])
            light = int(row["light"])
            target = float(row["target_brightness"])
            user_id = row["user_id"]
            
            # Train ALL rooms with this data so they are all smart
            for room_name, learner in rooms.items():
                # We use a dummy user_locations dict to satisfy the signature
                # but for pre-training raw data we just want to learn the mapping
                learner.learn(
                    hour, motion, light, target, 
                    user_id=user_id, 
                    user_locations={user_id: "Pretrain_Location"} 
                )
            count += 1
        except ValueError:
            continue
            
    print(f"✅ Trained {count} samples into all 3 room models.")
    print("💾 Models saved to models/ directory.")

if __name__ == "__main__":
    pretrain()
