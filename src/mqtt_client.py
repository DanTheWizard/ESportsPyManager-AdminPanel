import paho.mqtt.client as mqtt
from config import *
from datetime import datetime
from threading import Thread
import time
from collections import deque
from datetime import datetime, timedelta


connected_devices = set()   # Will contain active machine_ids
hostnames = {}              # machine_id -> hostname
last_active = {}            # machine_id -> datetime
device_status = {}          # machine_id → { cpu, ram, user, app }

# History storage
history_window = timedelta(minutes=AVG_PERSIST_MINUTES)
history_samples = deque()   # (timestamp, avg_cpu, avg_ram)


MQTT_TOPIC = "PC/#"
LASTACTIVE_TOPIC = "LastActive/#"

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, transport="websockets")

def on_connect(wsclient, userdata, flags, reason_code, properties):
    print("[MQTT] Connected")
    wsclient.subscribe(MQTT_TOPIC)
    wsclient.subscribe(LASTACTIVE_TOPIC)



def on_message(wsclient, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()
    if topic.startswith("PC/"):
        machine_id = topic.split('/')[1]
        connected_devices.add(machine_id) # Detects the computers by MACHINE_ID
        parts = topic.split('/')

        if len(parts) >= 2:
            machine_id = parts[1]
            connected_devices.add(machine_id)

            if len(parts) == 3 and parts[2] == "hostname":
                hostnames[machine_id] = payload

        if len(parts) == 3:
            machine_id = parts[1]
            key = parts[2]
            if key in ["cpu", "ram", "user", "app"]:
                device_status.setdefault(machine_id, {})[key] = payload

    elif topic.startswith("LastActive/") and topic.endswith("/time"):
        _, machine_id, _ = topic.split('/')
        last_active[machine_id] = datetime.now()
        #print(f"[MQTT] {machine_id} last seen at {last_active[machine_id]}")


def run_mqtt_and_stats():
    def mqtt_loop():
        client.loop_forever()

    Thread(target=mqtt_loop, daemon=True).start()

    if ENABLE_DASH_CHART:
        while True:
            update_average_history()
            time.sleep(CALC_CHART_AVG_TIMEOUT)

def mqtt_background_loop():
    client.username_pw_set(username=WS_USERNAME, password=WS_PASSWORD)
    if WS_USE_TLS:
        client.tls_set(ca_certs=None, certfile=None, keyfile=None)
    client.on_message = on_message
    client.on_connect = on_connect

    print("[MQTT] Connecting...")
    try:
        client.connect(WS_SERVER, WS_PORT)
    except Exception as e:
        print("ERROR: Unable to connect to WebSocket Server")
        print(f"Because: {e}")
        exit()

    run_mqtt_and_stats()  # <- replaces loop_forever()



def update_average_history():
    timestamp = datetime.now()
    cpu_values = [float(d.get("cpu", 0)) for d in device_status.values()]
    ram_values = [float(d.get("ram", 0)) for d in device_status.values()]
    if not cpu_values:
        return

    avg_cpu = sum(cpu_values) / len(cpu_values)
    avg_ram = sum(ram_values) / len(ram_values)

    history_samples.append((timestamp, avg_cpu, avg_ram))

    # Trim old entries
    cutoff = timestamp - history_window
    while history_samples and history_samples[0][0] < cutoff:
        history_samples.popleft()

    # print(f"[DEBUG] Appended history sample: CPU={avg_cpu:.2f}%, RAM={avg_ram:.2f}% at {timestamp.strftime('%H:%M:%S')}")

