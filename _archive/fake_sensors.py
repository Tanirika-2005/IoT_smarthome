# fake_sensors.py
import paho.mqtt.client as mqtt
import time
import random

BROKER = "localhost"
client = mqtt.Client()
client.connect(BROKER, 1883, 60)

print("Starting fake sensors (simulated 24h day)...\n")

sim_hour = 0

while True:

    hour = sim_hour

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

    client.publish("home/sensor/hour", str(hour))
    client.publish("home/sensor/motion", str(motion))
    client.publish("home/sensor/light", str(light_level))

    print(f"📡 Sensors → hour={hour:02d}, motion={motion}, light={light_level:03d}")

    sim_hour = (sim_hour + 1) % 24
    time.sleep(3)
