import gymnasium as gym
from gymnasium import spaces
import numpy as np
import random

class SmartHomeEnv(gym.Env):
    """
    Custom Environment that follows gym interface.
    The agent controls the brightness to balance energy saving and user comfort.
    """
    metadata = {'render.modes': ['human']}

    def __init__(self):
        super(SmartHomeEnv, self).__init__()
        
        # Actions: 0=Decrease(-10%), 1=Decrease(-5%), 2=NoChange, 3=Increase(+5%), 4=Increase(+10%)
        self.action_space = spaces.Discrete(5)
        
        # Observation Space:
        # [hour (0-24), motion (0/1), ambient_light (0-100), current_brightness (0-100), energy_consumed (accumulated)]
        # Normalized to roughly [0, 1] or similar ranges for stability
        self.observation_space = spaces.Box(
            low=np.array([0, 0, 0, 0, 0]), 
            high=np.array([24, 1, 100, 100, np.inf]),
            dtype=np.float32
        )
        
        self.state = None
        self.current_step = 0
        self.max_steps = 24 * 60  # Simulate one day (minutes)
        self.user_comfort_threshold = 5.0 # Tolerance for brightness difference
        
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.current_step = 0
        # Initial state: Midnight, No motion, Dark, Light Off, 0 Energy
        self.state = np.array([0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float32)
        return self.state, {}
    
    def step(self, action):
        self.current_step += 1
        
        hour, motion, ambient, current_brightness, energy = self.state
        
        # 1. Update Environment State (Simulation)
        # Simulate time passing
        hour = (self.current_step // 60) % 24
        
        # Simulate random motion (more likely in evening/morning)
        if 7 <= hour <= 9 or 18 <= hour <= 22:
            motion = 1.0 if random.random() > 0.3 else 0.0
        else:
            motion = 1.0 if random.random() > 0.8 else 0.0
            
        # Simulate ambient light (day/night cycle)
        if 6 <= hour <= 18:
            # Peak at noon
            ambient = 100.0 * np.sin((hour - 6) * np.pi / 12)
        else:
            ambient = 0.0
        
        # 2. Apply Action
        change = 0
        if action == 0: change = -10
        elif action == 1: change = -5
        elif action == 2: change = 0
        elif action == 3: change = +5
        elif action == 4: change = +10
        
        new_brightness = np.clip(current_brightness + change, 0, 100)
        
        # 3. Calculate Reward
        # Energy Cost: Higher brightness = higher cost
        energy_cost = (new_brightness / 100.0) * 0.1 
        
        # User Comfort Penalty:
        # Define "Ideal" brightness (Ground Truth for simulation)
        # If motion=1 and dark, user wants light. If motion=0, user wants dark.
        ideal_brightness = 0.0
        if motion == 1:
            if ambient < 40:
                ideal_brightness = 80.0
            elif ambient < 70:
                ideal_brightness = 40.0
            else:
                ideal_brightness = 0.0
        
        comfort_penalty = abs(new_brightness - ideal_brightness) * 0.05
        
        # Total Reward
        reward = -energy_cost - comfort_penalty
        
        # Update state
        energy += energy_cost
        self.state = np.array([hour, motion, ambient, new_brightness, energy], dtype=np.float32)
        
        # Check done
        terminated = self.current_step >= self.max_steps
        truncated = False
        
        info = {
            "energy_cost": energy_cost,
            "comfort_penalty": comfort_penalty,
            "ideal_brightness": ideal_brightness
        }
        
        return self.state, reward, terminated, truncated, info

    def render(self, mode='human'):
        print(f"Step: {self.current_step}, State: {self.state}")
