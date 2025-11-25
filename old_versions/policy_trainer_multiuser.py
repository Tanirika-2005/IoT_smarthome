import paho.mqtt.client as mqtt
import time

"""
Multi-user policy trainer for generating clean conflict-scenario datasets.
Different users have different brightness preferences.
"""

BROKER = "localhost"

# Sensor context
context = {
    "hour": 0,
    "motion": 0,
    "light": 50,
}

# User locations and activities
user_context = {
    "parent": {"location": None, "activity": None},
    "child": {"location": None, "activity": None},
    "guest": {"location": None, "activity": None},
}

# Per-user brightness policies
def get_brightness_preference(user_id, hour, motion, light_level):
    """
    Different users have different brightness preferences.
    parent: Likes bright light
    child: Prefers medium light
    guest: Standard/neutral policy
    """
    if motion == 0:
        # All users agree: lights off when no motion
        return 0.0
    
    # When motion is detected, preferences differ
    if user_id == "parent":
        # Parent prefers bright light
        if light_level < 20:
            return 80.0
        elif 20 <= light_level < 60:
            return 70.0
        else:
            return 40.0
    
    elif user_id == "child":
        # Child prefers medium brightness
        if light_level < 20:
            return 60.0
        elif 20 <= light_level < 60:
            return 50.0
        else:
            return 30.0
    
    elif user_id == "guest":
        # Guest uses standard policy (between parent and child)
        if light_level < 20:
            return 70.0
        elif 20 <= light_level < 60:
            return 60.0
        else:
            return 35.0
    
    return 50.0  # Fallback

def should_send_preference(user_id, hour, user_location, user_activity):
    """Determine if a user should send a brightness preference at this time."""
    if user_location is None or user_activity is None:
        return False  # User not active
    
    # Users only adjust brightness when active and in shared spaces
    if user_location in ["Living_Room", "Kitchen"]:
        return True
    
    # Users in their own room also adjust
    if user_id == "child" and user_location == "Bedroom":
        return True
    if user_id == "parent" and user_location == "Bedroom":
        return True
    if user_id == "guest" and user_location == "Guest_Room":
        return True
    
    return False

def on_connect(client, userdata, flags, rc):
    print("=" * 70)
    print("📚 Multi-User Policy Trainer (Conflict Dataset Generator)")
    print("=" * 70)
    print("Subscribing to sensors and user context...")
    print("Will publish brightness preferences to:")
    print("  - home/user/{user_id}/brightness_pref")
    print("=" * 70 + "\n")
    
    client.subscribe("home/sensor/#")
    client.subscribe("home/user/+/location")
    client.subscribe("home/user/+/activity")

def on_message(client, userdata, msg):
    global context, user_context
    
    topic = msg.topic
    payload = msg.payload.decode()
    
    # Update sensor context
    if topic == "home/sensor/hour":
        context["hour"] = int(payload)
    elif topic == "home/sensor/motion":
        context["motion"] = int(payload)
    elif topic == "home/sensor/light":
        context["light"] = int(payload)
        
        # When light sensor updates, compute and send user preferences
        process_user_preferences(client)
    
    # Update user context
    if topic.startswith("home/user/") and "/location" in topic:
        user_id = topic.split("/")[2]
        if user_id in user_context:
            user_context[user_id]["location"] = payload
    
    if topic.startswith("home/user/") and "/activity" in topic:
        user_id = topic.split("/")[2]
        if user_id in user_context:
            user_context[user_id]["activity"] = payload

def process_user_preferences(client):
    """Process and publish brightness preferences for all active users."""
    hour = context["hour"]
    motion = context["motion"]
    light = context["light"]
    
    active_users = []
    
    for user_id, uctx in user_context.items():
        if should_send_preference(user_id, hour, uctx["location"], uctx["activity"]):
            brightness = get_brightness_preference(user_id, hour, motion, light)
            
            # Publish user's preference
            client.publish(f"home/user/{user_id}/brightness_pref", str(brightness))
            active_users.append(f"{user_id}→{brightness:.0f}")
            
            print(
                f"📊 Policy: {user_id:8s} @ {uctx['location']:15s} "
                f"(h={hour:02d}, m={motion}, L={light:3d}) → {brightness:.0f}%"
            )
    
    if len(active_users) > 1:
        print(f"  🔥 CONFLICT: {', '.join(active_users)}\n")
    elif len(active_users) == 1:
        print()

def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, 1883, 60)
    
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 Policy trainer stopped.")
        client.disconnect()

if __name__ == "__main__":
    main()
