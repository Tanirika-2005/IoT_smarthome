import gymnasium as gym
from stable_baselines3 import DQN
from smart_home_env import SmartHomeEnv
import numpy as np

def run_benchmark():
    env = SmartHomeEnv()
    
    print("📊 Benchmarking RL Agent vs. Random Baseline")
    print("=" * 50)
    
    # 1. Random Baseline
    print("\n1. Random Agent (Baseline)")
    obs, _ = env.reset(seed=42)
    random_rewards = []
    random_energy = []
    random_discomfort = []
    
    for _ in range(1000):
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        random_rewards.append(reward)
        random_energy.append(info['energy_cost'])
        random_discomfort.append(info['comfort_penalty'])
        if terminated or truncated:
            obs, _ = env.reset()
            
    print(f"   Avg Reward: {np.mean(random_rewards):.4f}")
    print(f"   Avg Energy Cost: {np.mean(random_energy):.4f}")
    print(f"   Avg Discomfort: {np.mean(random_discomfort):.4f}")

    # 2. Trained RL Agent
    print("\n2. Trained DQN Agent")
    try:
        model = DQN.load("models/rl_policy")
    except:
        print("❌ Could not load model. Please train it first.")
        return

    obs, _ = env.reset(seed=42)
    rl_rewards = []
    rl_energy = []
    rl_discomfort = []
    
    for _ in range(1000):
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = env.step(action)
        rl_rewards.append(reward)
        rl_energy.append(info['energy_cost'])
        rl_discomfort.append(info['comfort_penalty'])
        if terminated or truncated:
            obs, _ = env.reset()

    print(f"   Avg Reward: {np.mean(rl_rewards):.4f}")
    print(f"   Avg Energy Cost: {np.mean(rl_energy):.4f}")
    print(f"   Avg Discomfort: {np.mean(rl_discomfort):.4f}")
    
    # Comparison
    print("\n📈 Improvement Analysis")
    print("-" * 30)
    reward_imp = (np.mean(rl_rewards) - np.mean(random_rewards)) / abs(np.mean(random_rewards)) * 100
    energy_imp = (np.mean(random_energy) - np.mean(rl_energy)) / np.mean(random_energy) * 100
    comfort_imp = (np.mean(random_discomfort) - np.mean(rl_discomfort)) / np.mean(random_discomfort) * 100
    
    print(f"   Reward Improvement: {reward_imp:+.2f}%")
    print(f"   Energy Savings:     {energy_imp:+.2f}%")
    print(f"   Comfort Gain:       {comfort_imp:+.2f}%")
    print("=" * 50)

if __name__ == "__main__":
    run_benchmark()
