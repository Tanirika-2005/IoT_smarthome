import os
import csv

import paho.mqtt.client as mqtt

BROKER = "localhost"
LOG_FILE = "brightness_training_log.csv"

# Keep the latest context seen from the sensors
context = {
    "hour": None,
    "motion": None,
    "light": None,
}


def ensure_log_header():
    """Ensure the CSV file exists and has the correct header."""
    needs_header = not os.path.exists(LOG_FILE) or os.path.getsize(LOG_FILE) == 0
    if needs_header:
        with open(LOG_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["hour", "motion", "light", "target_brightness"])


def log_sample(hour: int, motion: int, light: int, target: float) -> None:
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([hour, motion, light, float(target)])


def policy_brightness(hour: int, motion: int, light: int) -> float:
    """Deterministic policy used to generate a clean, paper-style dataset.

    - If no motion → lights off (0).
    - If motion and very dark (< 20) → bright (80).
    - If motion and medium light (20–59) → medium (60).
    - If motion and bright (>= 60) → low (30).
    """
    if motion == 0:
        return 0.0
    if light < 20:
        return 80.0
    if light < 60:
        return 60.0
    return 30.0


def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker for policy trainer.")
    client.subscribe("home/sensor/hour")
    client.subscribe("home/sensor/motion")
    client.subscribe("home/sensor/light")


def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()

    if topic.endswith("hour"):
        context["hour"] = int(payload)
    elif topic.endswith("motion"):
        context["motion"] = int(payload)
    elif topic.endswith("light"):
        context["light"] = int(payload)

    if None in context.values():
        return

    hour = int(context["hour"])
    motion = int(context["motion"])
    light = int(context["light"])

    target = policy_brightness(hour, motion, light)
    log_sample(hour, motion, light, target)
    print(
        f"Policy trainer logged: h={hour:02d}, m={motion}, L={light:03d} "
        f"→ target={target:.1f}"
    )


def main():
    ensure_log_header()

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, 1883, 60)

    print("Starting policy trainer (rule-based label generator)...")
    client.loop_forever()


if __name__ == "__main__":
    main()
