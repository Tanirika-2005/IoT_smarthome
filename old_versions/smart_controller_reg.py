import paho.mqtt.client as mqtt
import random
from brightness_learner import learner

BROKER = "localhost"
context = {"hour": 0, "motion": 0, "light": 50}
auto_mode = True

def on_connect(client, userdata, flags, rc):
    print("="  * 68)
    print("🤖 Smart Brightness Controller (Multi-User + SGDRegressor)")
    print("=" * 68)
    print("Commands:")
    print("  'b <value> [user_id]' → Teach brightness (0-100) for current context")
    print("                          e.g., 'b 80' or 'b 60 parent' or 'b 20 child'")
    print("  'i'                   → Show model weights/info")
    print("  'a'                   → Toggle auto mode")
    print("  'auto <n> [user_id]'  → Auto-train n samples (optional user)")
    print("  'q'                   → Quit")
    print("=" * 68 + "\n")
    client.subscribe("home/sensor/#")
    client.subscribe("home/training/brightness")
    client.subscribe("home/user/+/brightness_pref")  # Multi-user preferences

def on_message(client, userdata, msg):
    global context, auto_mode
    topic = msg.topic
    payload = msg.payload.decode()

    # Multi-user brightness preference from MQTT
    if topic.startswith("home/user/") and topic.endswith("/brightness_pref"):
        try:
            user_id = topic.split("/")[2]  # Extract user_id from topic
            val = float(payload)
            val = max(0.0, min(100.0, val))
            learner.learn(
                context["hour"],
                context["motion"],
                context["light"],
                val,
                user_id=user_id
            )
            client.publish("home/device/light/brightness", str(int(val)))
            client.publish("home/conflict/brightness", 
                          f"User {user_id} set brightness to {val:.1f}%")
            print(f"👤 [{user_id}] Taught brightness from MQTT → {val:.1f}%\n")
        except Exception as e:
            print(f"Failed to train from multi-user MQTT: {e}\n")
        return

    if topic == "home/training/brightness":
        try:
            val = float(payload)
            val = max(0.0, min(100.0, val))
            learner.learn(
                context["hour"],
                context["motion"],
                context["light"],
                val,
                user_id="default_user"
            )
            client.publish("home/device/light/brightness", str(int(val)))
            print(f"👤 Taught brightness from HA UI → {val:.1f}%\n")
        except Exception as e:
            print(f"Failed to train from HA UI: {e}\n")
        return

    if topic.endswith("hour"):
        context["hour"] = int(payload)
    elif topic.endswith("motion"):
        context["motion"] = int(payload)
    elif topic.endswith("light"):
        context["light"] = int(payload)

        if auto_mode:
            brightness = learner.predict(
                context["hour"],
                context["motion"],
                context["light"]
            )
            b_int = int(brightness)
            client.publish("home/device/light/brightness", str(b_int))
            print(f"💡 Auto brightness → {b_int}%\n")

def print_model_info():
    info = learner.get_model_info()
    if not info:
        print("No model info (not trained yet).\n")
        return
    print("\n" + "=" * 52)
    print("📊 Brightness Regression Model Info")
    print("=" * 52)
    for k, v in info["weights"].items():
        print(f"{k:>10}: {v:+.5f}")
    print(f"samples : {info['samples']}")
    print("=" * 52 + "\n")

def user_input_loop(client):
    global auto_mode
    while True:
        try:
            cmd = input("Command [b <0-100> [user] / i / a / auto / q]: ").strip().lower()

            if cmd == "q":
                learner.save_model()
                client.disconnect()
                break

            elif cmd == "a":
                auto_mode = not auto_mode
                print(f"Auto mode: {'ON' if auto_mode else 'OFF'}\n")

            elif cmd == "i":
                print_model_info()

            elif cmd.startswith("b "):
                try:
                    parts = cmd.split()
                    val = float(parts[1])
                    val = max(0.0, min(100.0, val))
                    user_id = parts[2] if len(parts) > 2 else "default_user"
                    
                    learner.learn(
                        context["hour"],
                        context["motion"],
                        context["light"],
                        val,
                        user_id=user_id
                    )
                    client.publish("home/device/light/brightness", str(int(val)))
                    client.publish("home/conflict/brightness", 
                                  f"User {user_id} set brightness to {val:.1f}%")
                    print(f"👤 [{user_id}] Taught brightness → {val:.1f}%\n")
                except Exception:
                    print("Invalid command. Use: b <0-100> [user_id]\n")

            elif cmd.startswith("auto"):
                # Usage: auto <n_samples> [user_id]
                try:
                    parts = cmd.split()
                    n_samples = int(parts[1]) if len(parts) > 1 else 50
                    user_id = parts[2] if len(parts) > 2 else "default_user"

                    for _ in range(n_samples):
                        # choose a random brightness in [0,100], biased toward typical values
                        val = random.choice([0, 20, 40, 60, 80, 100])
                        learner.learn(
                            context["hour"],
                            context["motion"],
                            context["light"],
                            val,
                            user_id=user_id
                        )

                    print(
                        f"Auto-trained {n_samples} random samples for user '{user_id}' "
                        f"at context (h={context['hour']}, "
                        f"m={context['motion']}, L={context['light']}).\n"
                    )
                except Exception:
                    print("Usage: auto <n_samples> [user_id] (e.g., auto 50 parent)\n")

            else:
                print("Invalid command.\n")

        except KeyboardInterrupt:
            learner.save_model()
            client.disconnect()
            break
        except Exception as e:
            print(f"Error: {e}\n")

def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, 1883, 60)

    client.loop_start()
    try:
        user_input_loop(client)
    finally:
        client.loop_stop()

if __name__ == "__main__":
    main()
