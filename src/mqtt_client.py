import paho.mqtt.client as mqtt
from config import *
from threading import Thread
import time

connected_devices = set()   # Will contain active machine_ids
hostnames = {}              # machine_id -> hostname

MQTT_TOPIC = "PC/#"


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, transport="websockets")

def on_connect(wsclient, userdata, flags, reason_code, properties):
    print("[MQTT] Connected")
    wsclient.subscribe(MQTT_TOPIC)



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

def mqtt_background_loop():
    client.username_pw_set(username=WS_USERNAME, password=WS_PASSWORD)
    if WS_USE_TLS: client.tls_set(ca_certs=None, certfile=None, keyfile=None)  # Use system CA certificates (no ca_certs needed) based on config
    client.on_message = on_message
    client.on_connect = on_connect

    print("[MQTT] Connecting...")
    try:
        client.connect(WS_SERVER, WS_PORT)
    except Exception as e:
        print("ERROR: Unable to connect to WebSocket Server")
        print(f"Because: {e}")
        exit()
    client.loop_forever()  # blocking call inside thread
