#!/usr/bin/env python3
"""
Multi-Room Sensor Simulator
Simulates 24-hour cycle with realistic room-specific user activity patterns.
"""

import paho.mqtt.client as mqtt
import time
import random

BROKER = "localhost"
SPEED_MULTIPLIER = 1  # Real-time simulation (1 real second = 1 simulated second)

def publish_context(client, hour):
    """Publish environmental context"""
    # Motion: higher during wake hours
    motion = 1 if 6 <= hour <= 23 else random.choice([0, 1])
    
    # Light: based on time of day
    if 6 <= hour < 18:
        light = random.randint(60, 90)  # Daytime: bright
    elif 18 <= hour < 22:
        light = random.randint(40, 60)  # Evening: medium
    else:
        light = random.randint(10, 30)  # Night: dim
    
    client.publish("home/sensor/hour", str(hour))
    client.publish("home/sensor/motion", str(motion))
    client.publish("home/sensor/light", str(light))

def get_user_locations(hour):
    """Get realistic user locations based on time of day"""
    
    # Morning (6-9): Bedroom → Kitchen transition
    if 6 <= hour < 9:
        return {
            "parent": random.choice(["Bedroom", "Kitchen"]),
            "child": "Bedroom",
            "guest": "Bedroom"
        }
    
    # Day (9-17): Distributed
    elif 9 <= hour < 17:
        return {
            "parent": random.choice(["Kitchen", "Living_Room"]),
            "child": random.choice(["Living_Room", "Bedroom"]),
            "guest": random.choice(["Living_Room", "Kitchen"])
        }
    
    # Evening (17-22): Living Room family time
    elif 17 <= hour < 22:
        return {
            "parent": "Living_Room",
            "child": "Living_Room",
            "guest": random.choice(["Living_Room", "Bedroom"])
        }
    
    # Night (22-6): Bedroom
    else:
        return {
            "parent": "Bedroom",
            "child": "Bedroom",
            "guest": "Bedroom"
        }

def main():
    client = mqtt.Client()
    client.connect(BROKER, 1883, 60)
    client.loop_start()
    
    print("🌍 Multi-Room Sensor Simulator")
    print("=" * 60)
    print(f"Speed: {SPEED_MULTIPLIER}x (1 sec = 1 min)")
    print("Rooms: Living_Room, Bedroom, Kitchen")
    print("=" * 60 + "\n")
    
    hour = 0
    
    try:
        while True:
            # Publish context
            publish_context(client, hour)
            
            # Publish user locations
            locations = get_user_locations(hour)
            for user, location in locations.items():
                client.publish(f"home/user/{user}/location", location)
            
            # Print status
            time_str = f"{hour:02d}:00"
            loc_str = ", ".join([f"{u}@{l}" for u, l in locations.items()])
            print(f"⏰ {time_str} | {loc_str}")
            
            # Next hour
            time.sleep(1 / SPEED_MULTIPLIER)
            hour = (hour + 1) % 24
            
    except KeyboardInterrupt:
        print("\n\n✓ Stopped simulator")
    
    client.loop_stop()

if __name__ == "__main__":
    main()
