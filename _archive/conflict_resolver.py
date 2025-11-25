import paho.mqtt.client as mqtt

BROKER = "localhost"

context = {
    "user1_activity": None,
    "user1_location": None,
    "user2_activity": None,
    "user2_location": None,
}


def resolve_conflict(message: str):
    # Simple policy:
    # - Assume conflict is about a shared device in the Living_Room
    # - Prefer the user currently in the Living_Room
    # - If both in same room, prefer the one who has been active (non-None activity)
    # - Fallback: user1
    u1_loc = context.get("user1_location")
    u2_loc = context.get("user2_location")
    u1_act = context.get("user1_activity")
    u2_act = context.get("user2_activity")

    if u1_loc == "Living_Room" and u2_loc != "Living_Room":
        winner = "user1"
    elif u2_loc == "Living_Room" and u1_loc != "Living_Room":
        winner = "user2"
    else:
        # Same room or unknown; prefer the user who is currently active
        if u1_act and not u2_act:
            winner = "user1"
        elif u2_act and not u1_act:
            winner = "user2"
        else:
            winner = "user1"

    if winner == "user1":
        loser = "user2"
    else:
        loser = "user1"

    resolution = (
        f"Conflict detected: '{message}'. "
        f"Resolved in favor of {winner} "
        f"(locations: user1={u1_loc}, user2={u2_loc}; "
        f"activities: user1={u1_act}, user2={u2_act})."
    )
    return resolution, winner, loser


def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker for conflict resolution.")
    client.subscribe("home/user1/activity")
    client.subscribe("home/user1/location")
    client.subscribe("home/user2/activity")
    client.subscribe("home/user2/location")
    client.subscribe("home/conflict")


def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()

    if topic == "home/user1/activity":
        context["user1_activity"] = payload
    elif topic == "home/user1/location":
        context["user1_location"] = payload
    elif topic == "home/user2/activity":
        context["user2_activity"] = payload
    elif topic == "home/user2/location":
        context["user2_location"] = payload
    elif topic == "home/conflict":
        resolution, winner, loser = resolve_conflict(payload)
        print(resolution)
        client.publish("home/conflict/resolution", resolution)


def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, 1883, 60)

    client.loop_forever()


if __name__ == "__main__":
    main()
