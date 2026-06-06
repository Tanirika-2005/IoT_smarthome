import gymnasium as gym
from stable_baselines3 import DQN
from stable_baselines3.common.callbacks import EvalCallback
from smart_home_env import SmartHomeEnv
import os

def train_agent():
    # Create environment
    env = SmartHomeEnv()
    
    # Define model
    model = DQN(
        "MlpPolicy", 
        env, 
        verbose=1,
        learning_rate=1e-3,
        buffer_size=50000,
        learning_starts=1000,
        batch_size=32,
        gamma=0.99,
        train_freq=4,
        gradient_steps=1,
        target_update_interval=1000,
        exploration_fraction=0.1,
        exploration_final_eps=0.02,
        tensorboard_log="./rl_logs/"
    )
    
    # Train
    print("🚀 Starting RL Training...")
    model.learn(total_timesteps=20000, log_interval=10)
    
    # Save
    os.makedirs("models", exist_ok=True)
    model.save("models/rl_policy")
    print("💾 Model saved to models/rl_policy.zip")
    
    # Evaluate
    print("\n🔍 Evaluating Agent...")
    obs, _ = env.reset()
    total_reward = 0
    for i in range(100):
        action, _states = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += reward
        if i % 10 == 0:
            print(f"Step {i}: Action={action}, Reward={reward:.2f}, Info={info}")
        if terminated or truncated:
            obs, _ = env.reset()
            
    print(f"Average Reward per step: {total_reward/100:.4f}")

if __name__ == "__main__":
    train_agent()
