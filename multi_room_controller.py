#!/usr/bin/env python3
"""
Multi-Room Brightness Controller
Manages separate AI models for each room (Living_Room, Bedroom, Kitchen).
Each model only learns from users physically present in that room.
"""

import paho.mqtt.client as mqtt
from brightness_learner import BrightnessLearner
import os

BROKER = "localhost"

# Global state
rooms = {}
context = {"hour": 0, "motion": 0, "light": 50}
user_locations = {}

def init_rooms():
    """Initialize separate BrightnessLearner for each room"""
    global rooms
    
    room_configs = [
        ("living_room", "Living_Room"),
        ("bedroom", "Bedroom"),
        ("kitchen", "Kitchen")
    ]
    
    print(f"DEBUG: Current CWD is {os.getcwd()}")
    
    for room_id, room_display in room_configs:
        learner = BrightnessLearner(
            model_file=f"models/{room_id}_model.pkl",
            location_boost=1
        )
        learner.device_location = room_display  # Set room name
        rooms[room_id] = learner
    
    print("✅ Initialized 3 room models:")
    for room_id, learner in rooms.items():
        print(f"   • {learner.device_location}: {learner.model_file}")

def on_connect(client, userdata, flags, rc):
    print("=" * 70)
    print("🏠 Multi-Room Brightness Controller")
    print("=" * 70)
    print(f"✓ Connected to MQTT broker")
    print(f"✓ Managing {len(rooms)} rooms: Living_Room, Bedroom, Kitchen")
    print(f"✓ Room isolation: Users only control lights in their current room")
    print("=" * 70 + "\n")
    
    # Subscribe to all topics
    client.subscribe("home/sensor/#")
    client.subscribe("home/user/+/+/brightness_pref")  # user_id/room/brightness_pref
    client.subscribe("home/user/+/location")
    print("📡 Subscribed to MQTT topics\n")

def on_message(client, userdata, msg):
    global context, user_locations
    topic = msg.topic
    payload = msg.payload.decode()
    
    # User brightness preference for specific room
    # Format: home/user/{user_id}/{room}/brightness_pref
    if "brightness_pref" in topic:
        try:
            parts = topic.split("/")
            user_id = parts[2]  # e.g., "parent"
            room_id = parts[3]  # e.g., "living_room"
            brightness = float(payload)
            brightness = max(0.0, min(100.0, brightness))
            
            if room_id in rooms:
                print(f"📥 {user_id} → {room_id}: {brightness:.0f}%")
                
                # Train room-specific model
                learner = rooms[room_id]
                learner.learn(
                    context["hour"],
                    context["motion"],
                    context["light"],
                    brightness,
                    user_id=user_id,
                    user_locations=user_locations
                )
                
                # Predict and publish for this room
                predicted = learner.predict(
                    context["hour"],
                    context["motion"],
                    context["light"]
                )
                
                client.publish(f"home/device/{room_id}/light/brightness", str(int(predicted)))
                print(f"✅ {room_id} → {predicted:.0f}%\n")
            else:
                print(f"⚠️  Unknown room: {room_id}")
                
        except Exception as e:
            print(f"❌ Error: {e}\n")
        return
    
    # User location updates
    if topic.startswith("home/user/") and topic.endswith("/location"):
        user_id = topic.split("/")[2]
        user_locations[user_id] = payload
        print(f"📍 {user_id} → {payload}")
        
        # Auto-predict for all rooms when location changes
        for room_id, learner in rooms.items():
            pred = learner.predict(context["hour"], context["motion"], context["light"])
            client.publish(f"home/device/{room_id}/light/brightness", str(int(pred)))
        return
    
    # Context updates (sensors)
    if topic.endswith("hour"):
        context["hour"] = int(payload)
    elif topic.endswith("motion"):
        context["motion"] = int(payload)
    elif topic.endswith("light"):
        context["light"] = int(payload)
        
        # Auto-predict for all rooms when context changes
        for room_id, learner in rooms.items():
            pred = learner.predict(context["hour"], context["motion"], context["light"])
            client.publish(f"home/device/{room_id}/light/brightness", str(int(pred)))

def main():
    print("\n🚀 Starting Multi-Room Controller...\n")
    
    # Initialize room models
    init_rooms()
    
    # Setup MQTT client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    
    client.connect(BROKER, 1883, 60)
    print("\n🔄 Running... (Ctrl+C to stop)\n")
    client.loop_forever()

if __name__ == "__main__":
    main()
