#!/usr/bin/env python3
"""
Home Assistant Multi-User Brightness Controller
Headless version - runs in background, processes MQTT only
For demos and production use with Home Assistant UI
"""

import paho.mqtt.client as mqtt
from brightness_learner import learner

BROKER = "localhost"
context = {"hour": 0, "motion": 0, "light": 50}
user_locations = {}  # Track user locations for location-aware conflict resolution

def on_connect(client, userdata, flags, rc):
    print("=" * 68)
    print("🏠 Home Assistant Multi-User Brightness Controller (Headless)")
    print("=" * 68)
    print("✓ Connected to MQTT broker")
    print("✓ Listening for user preferences on: home/user/+/brightness_pref")
    print("✓ Publishing AI output to: home/device/light/brightness")
    print("✓ Conflict resolution enabled with priority: parent > child > guest")
    print("=" * 68 + "\n")
    
    # Subscribe to all relevant topics
    client.subscribe("home/sensor/#")
    client.subscribe("home/user/+/brightness_pref")
    client.subscribe("home/user/+/location")
    client.subscribe("home/user/+/activity")
    print("📡 Subscribed to MQTT topics. Ready to process user inputs!\n")

def on_message(client, userdata, msg):
    global context, user_locations
    topic = msg.topic
    payload = msg.payload.decode()

    # Multi-user brightness preference from Home Assistant sliders
    if topic.startswith("home/user/") and topic.endswith("/brightness_pref"):
        try:
            user_id = topic.split("/")[2]  # Extract user_id from topic
            val = float(payload)
            val = max(0.0, min(100.0, val))
            
            print(f"📥 Received: {user_id} → {val:.1f}%")
            
            # Process through learner (handles conflict resolution with location awareness)
            learner.learn(
                context["hour"],
                context["motion"],
                context["light"],
                val,
                user_id=user_id,
                user_locations=user_locations
            )
            
            # Publish resolved brightness back to HA
            # Note: learner may have resolved conflicts, so get the actual prediction
            resolved_brightness = learner.predict(
                context["hour"],
                context["motion"],
                context["light"]
            )
            
            client.publish("home/device/light/brightness", str(int(resolved_brightness)))
            
            # Publish conflict status
            conflict_msg = f"User '{user_id}' set preference to {val:.1f}% → AI output: {resolved_brightness:.0f}%"
            client.publish("home/conflict/brightness", conflict_msg)
            
            print(f"✅ Processed: AI output → {resolved_brightness:.0f}%")
            print(f"   Context: h={context['hour']}, m={context['motion']}, L={context['light']}\n")
            
        except Exception as e:
            print(f"❌ Error processing user preference: {e}\n")
        return

    # Update context from sensor data
    if topic.endswith("hour"):
        context["hour"] = int(payload)
        print(f"🕐 Hour updated: {context['hour']}")
    elif topic.endswith("motion"):
        context["motion"] = int(payload)
        print(f"👁️  Motion updated: {context['motion']}")
    elif topic.endswith("light"):
        context["light"] = int(payload)
        print(f"💡 Light updated: {context['light']}")
        
        # Auto-predict when context changes
        brightness = learner.predict(
            context["hour"],
            context["motion"],
            context["light"]
        )
        client.publish("home/device/light/brightness", str(int(brightness)))
        print(f"🤖 Auto-prediction: {brightness:.0f}%\n")
    
    # Track user locations for location-aware conflict resolution
    elif topic.startswith("home/user/") and topic.endswith("/location"):
        user_id = topic.split("/")[2]
        user_locations[user_id] = payload
        print(f"📍 {user_id} location: {payload}")

def main():
    print("\n🚀 Starting Home Assistant Multi-User Controller...\n")
    
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect(BROKER, 1883, 60)
        print("✓ Connected to MQTT broker at localhost:1883\n")
    except Exception as e:
        print(f"❌ Failed to connect to MQTT broker: {e}")
        print("   Make sure mosquitto is running!")
        return
    
    # Run forever, processing MQTT messages
    print("🔄 Running... (Press Ctrl+C to stop)\n")
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down gracefully...")
        client.disconnect()

if __name__ == "__main__":
    main()
