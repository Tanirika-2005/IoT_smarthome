import gymnasium as gym
from stable_baselines3 import DQN
from smart_home_env import SmartHomeEnv
import numpy as np

def trace_episode():
    env = SmartHomeEnv()
    model_path = "models/rl_policy"
    
    print("🕵️  Tracing RL Agent Behavior (One Episode)")
    print("==========================================")
    
    try:
        model = DQN.load(model_path)
    except:
        print("❌ Model not found. Train it first.")
        return

    obs, _ = env.reset(seed=42)
    terminated = False
    truncated = False
    step = 0
    
    print(f"{'Step':<5} | {'Hour':<4} | {'Light':<5} | {'Action':<15} | {'Brightness':<10} | {'Energy Cost':<11} | {'Reward':<8}")
    print("-" * 85)
    
    total_reward = 0
    
    while not (terminated or truncated) and step < 20: # Show first 20 steps
        action, _ = model.predict(obs, deterministic=True)
        
        # Decode action for display
        # Actions: 0=Decr(-10), 1=Decr(-5), 2=Same, 3=Incr(+5), 4=Incr(+10)
        action_map = {0: "⬇️ -10%", 1: "↘️ -5%", 2: "➡️ Hold", 3: "↗️ +5%", 4: "⬆️ +10%"}
        action_str = action_map.get(int(action), str(action))
        
        obs, reward, terminated, truncated, info = env.step(action)
        
        # Unpack state for display: [hour, motion, light, brightness, energy]
        hour = int(obs[0])
        light = int(obs[2])
        brightness = int(obs[3])
        energy_cost = info['energy_cost']
        
        print(f"{step:<5} | {hour:<4} | {light:<5} | {action_str:<15} | {brightness:<10} | {energy_cost:<11.4f} | {reward:<8.4f}")
        
        total_reward += reward
        step += 1
        
    print("-" * 85)
    print(f"Total Reward for this sequence: {total_reward:.4f}")
    print("\n💡 Analysis:")
    print("Notice how the agent adjusts brightness. It should aim for a balance.")
    print("If it keeps brightness too high, Energy Cost goes up and Reward goes down.")
    print("If it keeps it too low when needed, Comfort Penalty (part of Reward) would increase.")

if __name__ == "__main__":
    trace_episode()
