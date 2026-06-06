import torch
import os
from brightness_learner import BrightnessLearner

def demo_continuous_learning():
    print("🧠 Continuous Learning Demonstration")
    print("=" * 60)
    print("Scenario: It's 8:00 PM (Hour=20), Motion Detected, Dark Room (Light=10).")
    print("The user wants the light at 85%, but the model starts untrained.")
    print("-" * 60)

    # 1. Initialize fresh model (delete old one if exists for clean demo)
    if os.path.exists("demo_model.pth"):
        os.remove("demo_model.pth")
        
    learner = BrightnessLearner(model_file="demo_model.pth")
    
    # Context: 8 PM (20/24), Motion (1), Light (10/100)
    hour = 20
    motion = 1
    light = 10
    target = 85.0 # User wants it bright
    
    # 2. Loop to show learning
    for i in range(1, 6):
        print(f"\n[Interaction #{i}]")
        
        # A. Predict BEFORE learning
        pred = learner.predict(hour, motion, light)
        error = abs(pred - target)
        
        print(f"   🤖 Model Prediction: {pred:.1f}%")
        print(f"   👤 User Feedback:    {target:.1f}%")
        print(f"   📉 Error:            {error:.1f}%")
        
        # B. Learn (Update Weights)
        print("   ⚡ Updating model weights...")
        learner.learn(hour, motion, light, target, user_id="demo_user")
        
        # C. Verify improvement
        # In a real app, we'd see this next time. Here we check immediately to show the update.
        new_pred = learner.predict(hour, motion, light)
        improvement = abs(pred - target) - abs(new_pred - target)
        
        print(f"   🔄 New Prediction:   {new_pred:.1f}% (Improved by {improvement:.1f}%)")
        
        if abs(new_pred - target) < 2.0:
            print("\n✅ CONVERGED! The model has learned the user's preference.")
            break

    print("=" * 60)
    print("Proof: The model adapted from the initial prediction to the target")
    print("without retraining from scratch. This is Online Continuous Learning.")

if __name__ == "__main__":
    demo_continuous_learning()
