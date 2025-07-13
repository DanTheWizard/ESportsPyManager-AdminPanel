import paho.mqtt.client as mqtt
import time
import json
from config          import *
from threading       import Thread
from collections     import deque
from datetime        import datetime, timedelta
from src.database import get_all_device_status, get_online_devices, get_registered_devices, upsert_device_status
from src.database import update_last_seen

last_active = {}            # machine_id -> datetime


# History storage
history_window = timedelta(minutes=AVG_PERSIST_MINUTES)
history_samples = deque()   # (timestamp, avg_cpu, avg_ram)


MQTT_TOPIC = "PC/#"
LASTACTIVE_TOPIC = "LastActive/#"
ESPORTS_STATUS_TOPIC = "ESports/status"

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, transport="websockets")



# Connect to MQTT
def on_connect(wsclient, userdata, flags, reason_code, properties):
    print("[MQTT] Connected")
    wsclient.subscribe(MQTT_TOPIC)
    wsclient.subscribe(LASTACTIVE_TOPIC)
    wsclient.subscribe(ESPORTS_STATUS_TOPIC)



def on_message(wsclient, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()

    if topic.startswith("PC/") and topic.endswith("/data"):
        parts = topic.split('/')
        if len(parts) == 3:
            machine_id = parts[1]

            try:
                data = json.loads(payload)
                upsert_device_status(machine_id, data)
            except json.JSONDecodeError:
                print(f"[MQTT] Failed to decode JSON payload for {machine_id}: {payload}")

    elif topic == ESPORTS_STATUS_TOPIC:
        try:
            get_esports_status.last_status = json.loads(payload)
        except Exception:
            get_esports_status.last_status = None



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
    status_rows = get_all_device_status()

    cpu_values = []
    ram_values = []
    for row in status_rows:
        _, _, cpu, ram, *_ = row
        try:
            cpu_values.append(float(cpu))
            ram_values.append(float(ram))
        except (ValueError, TypeError):
            continue  # Skip invalid data

    if not cpu_values:
        return

    avg_cpu = sum(cpu_values) / len(cpu_values)
    avg_ram = sum(ram_values) / len(ram_values)

    registered_ids = {device[0] for device in get_registered_devices()}
    online_ids = get_online_devices()

    online_registered_count = sum(
        1 for machine_id in online_ids if machine_id in registered_ids
    )

    # Append the data to the history, including the device count
    history_samples.append((timestamp, avg_cpu, avg_ram, online_registered_count))

    # Trim old entries
    cutoff = timestamp - history_window
    while history_samples and history_samples[0][0] < cutoff:
        history_samples.popleft()

########################################################################################################################

def publish_esports_status(status_dict):
    payload = json.dumps(status_dict)
    # Publish with retain=True
    client.publish(ESPORTS_STATUS_TOPIC, payload, retain=True)

def get_esports_status():
    # This function should return the last retained message for the topic.
    # Since paho-mqtt does not provide a direct sync retained message fetch,
    # you need to subscribe and handle the message in a callback.
    # For a simple approach, cache the last received retained message:
    if not hasattr(get_esports_status, "last_status"):
        get_esports_status.last_status = None

    return get_esports_status.last_status