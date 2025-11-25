import paho.mqtt.client as mqtt
import time
import random

"""
Multi-user fake sensor simulator for testing conflict resolution.
Simulates 24-hour day with multiple users in different locations and activities.
"""

BROKER = "localhost"

# User profiles with different daily patterns
USERS = {
    "parent": {
        "active_hours": (6, 22),  # 6am - 10pm
        "common_locations": ["Living_Room", "Kitchen", "Bedroom"],
        "location_weights": [0.5, 0.3, 0.2],
    },
    "child": {
        "active_hours": (7, 21),  # 7am - 9pm
        "common_locations": ["Bedroom", "Living_Room", "Kitchen"],
        "location_weights": [0.4, 0.4, 0.2],
    },
    "guest": {
        "active_hours": (9, 18),  # Limited presence
        "common_locations": ["Living_Room", "Guest_Room"],
        "location_weights": [0.6, 0.4],
    },
}

def get_user_location(user_id, hour):
    """Determine user location based on time and profile."""
    profile = USERS[user_id]
    active_start, active_end = profile["active_hours"]
    
    if not (active_start <= hour < active_end):
        # User is sleeping/away
        if user_id == "guest":
            return None  # Guest not present
        else:
            return "Bedroom" if user_id == "parent" else "Bedroom"
    
    # During active hours, pick a location based on weights
    return random.choices(
        profile["common_locations"],
        weights=profile["location_weights"]
    )[0]

def get_user_activity(user_id, hour, location):
    """Determine user activity based on location and time."""
    if location is None:
        return None
    
    if location == "Bedroom":
        return "sleeping" if hour < 7 or hour >= 22 else "resting"
    elif location == "Kitchen":
        if 6 <= hour < 9:
            return "breakfast"
        elif 12 <= hour < 14:
            return "lunch"
        elif 18 <= hour < 20:
            return "dinner"
        else:
            return "snacking"
    elif location == "Living_Room":
        activities = ["watching_tv", "reading", "relaxing"]
        return random.choice(activities)
    elif location == "Guest_Room":
        return "resting"
    else:
        return "idle"

def get_sensor_context(hour):
    """Get motion and light sensor values based on hour (same as original fake_sensors.py)."""
    if 0 <= hour < 6:
        p_motion = 0.1
        light_min, light_max = 0, 20
    elif 6 <= hour < 12:
        p_motion = 0.4
        light_min, light_max = 20, 60
    elif 12 <= hour < 18:
        p_motion = 0.6
        light_min, light_max = 40, 100
    else:
        p_motion = 0.3
        light_min, light_max = 0, 60

    motion = 1 if random.random() < p_motion else 0
    light_level = random.randint(light_min, light_max)
    
    return motion, light_level

def on_connect(client, userdata, flags, rc):
    print("=" * 60)
    print("🏠 Multi-User Smart Home Sensor Simulator")
    print("=" * 60)
    print("Simulating 3 users: parent, child, guest")
    print("Publishing to:")
    print("  - home/sensor/hour")
    print("  - home/sensor/motion")
    print("  - home/sensor/light")
    print("  - home/user/{user_id}/location")
    print("  - home/user/{user_id}/activity")
    print("=" * 60 + "\n")

def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.connect(BROKER, 1883, 60)
    client.loop_start()
    
    sim_hour = 0
    
    try:
        while True:
            hour = sim_hour
            
            # Get sensor context
            motion, light_level = get_sensor_context(hour)
            
            # Publish sensor data
            client.publish("home/sensor/hour", str(hour))
            client.publish("home/sensor/motion", str(motion))
            client.publish("home/sensor/light", str(light_level))
            
            print(f"\n⏰ Hour {hour:02d}:00 | Motion={motion} | Light={light_level}")
            
            # Update each user's location and activity
            for user_id in USERS.keys():
                location = get_user_location(user_id, hour)
                activity = get_user_activity(user_id, hour, location)
                
                if location:
                    client.publish(f"home/user/{user_id}/location", location)
                    print(f"  👤 {user_id:8s} → {location:15s} ({activity})")
                if activity:
                    client.publish(f"home/user/{user_id}/activity", activity)
            
            # Highlight potential conflicts (multiple users in same location)
            locations = {}
            for user_id in USERS.keys():
                loc = get_user_location(user_id, hour)
                if loc:
                    if loc not in locations:
                        locations[loc] = []
                    locations[loc].append(user_id)
            
            for loc, users_in_loc in locations.items():
                if len(users_in_loc) > 1:
                    print(f"  ⚠️  POTENTIAL CONFLICT in {loc}: {', '.join(users_in_loc)}")
            
            # Advance simulation
            sim_hour = (sim_hour + 1) % 24
            time.sleep(3)  # 3 seconds per simulated hour
            
    except KeyboardInterrupt:
        print("\n\n🛑 Simulation stopped by user.")
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()
