from datetime        import datetime
from flask           import Blueprint, redirect, url_for, request, jsonify, current_app
from flask_login     import login_required
from src.database    import register_device, remove_device
from src.database    import (
    get_registered_devices,
    get_online_devices,
    get_all_device_status,
    get_last_seen
)
from src.mqtt_client import client as mqtt_client
from src.mqtt_client import get_esports_status, publish_esports_status, history_samples

from config          import *
import bleach



def sanitize_input(input_data):
    return bleach.clean(input_data, tags=[], attributes={}, strip=True)

# Usage


api_routes = Blueprint("api_routes", __name__, url_prefix="/api")

@api_routes.route('/dashboard_stats')
@login_required
def api_dashboard_stats():
    registered = get_registered_devices()
    registered_ids = {r[0] for r in registered}
    total = len(registered)

    online_ids = get_online_devices()
    online = sum(1 for id in online_ids if id in registered_ids)
    unregistered_online = sum(1 for id in online_ids if id not in registered_ids)

    return jsonify({
        "total": total,
        "online": online,
        "offline": total - online,
        "unregistered": unregistered_online
    })


@api_routes.route('/device_usage_data')
@login_required
def api_device_usage_data():
    usage = []
    online_ids = get_online_devices()
    registered = get_registered_devices()
    device_map = {d[0]: d[1] for d in registered}  # machine_id → nickname

    for row in get_all_device_status():
        machine_id, _, cpu, ram, _, _, _, _ = row
        if machine_id not in online_ids or machine_id not in device_map:
            continue

        try:
            cpu = float(cpu)
            ram = float(ram)
        except (TypeError, ValueError):
            cpu = ram = 0.0

        usage.append({
            "nickname": device_map[machine_id],
            "cpu": cpu,
            "ram": ram
        })

    return jsonify(devices=usage)


@api_routes.route("/avg_usage_history")
@login_required
def api_avg_usage_history():
    return jsonify([
        {
            "time": ts.strftime("%H:%M:%S"),
            "cpu": round(cpu, 2),
            "ram": round(ram, 2),
            "count": count
        }
        for ts, cpu, ram, count in history_samples
    ])


# Register and DeRegister
@api_routes.route('/register_from_manage', methods=['POST'])
@login_required
def register_from_manage():
    machine_id = sanitize_input(request.form.get("machine_id"))
    nickname   = sanitize_input(request.form.get("nickname"))
    tag        = sanitize_input(request.form.get("tag"))

    if machine_id and nickname:
        register_device(machine_id, nickname, tag)
        current_app.logger.info(f"Device {machine_id} registered as '{nickname}'")
    else:
        current_app.logger.error("Missing fields")

    return redirect(url_for('app_routes.manage_devices'))

@api_routes.route('/deregister', methods=['POST'])
@login_required
def deregister_device():
    machine_id = request.form.get("machine_id")
    if machine_id:
        remove_device(machine_id)
        current_app.logger.info(f"Device {machine_id} has been removed")
    return redirect(url_for('app_routes.manage_devices'))



# Send Actions to PC

@api_routes.route('/send_action', methods=['POST'])
@login_required
def send_action():
    machine_ids = request.form.getlist('selected_devices')
    action = request.form.get("bulk_action") or "none"
    argument = request.form.get("bulk_argument", "").strip()

    if not machine_ids:
        current_app.logger.warning("No devices selected for bulk action.")
        return redirect(url_for('app_routes.actions_page'))

    final_action = action
    if argument and action in ["shutdown", "say"]:
        final_action = f"{action}:{argument}"

    for machine_id in machine_ids:
        mqtt_client.publish(f"PC/{machine_id}/action", final_action)

    current_app.logger.info(f"Sent '{final_action}' to {len(machine_ids)} device(s).")
    return redirect(url_for('app_routes.actions_page'))



@api_routes.route('/send_action_device', methods=['POST'])
@login_required
def send_action_device():
    machine_id = request.form.get("machine_id")
    action     = request.form.get("action") or "none"
    argument   = request.form.get("argument", "").strip()

    if not machine_id:
        return jsonify(status="error", message="Missing machine_id"), 400

    final = action
    if argument and action in ["shutdown", "say"]:
        final = f"{action}:{argument}"

    mqtt_client.publish(f"PC/{machine_id}/action", final)
    return jsonify(status="success", sent=final, to=machine_id), 200



# Device Status
@api_routes.route('/device_statuses')
@login_required
def api_device_statuses():
    registered = get_registered_devices()
    online_ids = get_online_devices()

    statuses = []
    for machine_id, nickname, *_ , tag in registered:
        online = machine_id in online_ids
        statuses.append({
            "machine_id": machine_id,
            "tag": tag,
            "nickname": nickname,
            "online": online,
            "last_active": get_last_seen(machine_id)
        })
    return jsonify(statuses=statuses)





@api_routes.route('/unregistered_devices')
@login_required
def api_unregistered_devices():
    now = datetime.now()
    registered_ids = {device[0] for device in get_registered_devices()}
    online_ids = get_online_devices()

    unregistered = []
    for row in get_all_device_status():
        machine_id, hostname, *_ = row
        if machine_id in online_ids and machine_id not in registered_ids:
            unregistered.append({
                "machine_id": machine_id,
                "hostname": hostname or "Unknown"
            })

    unregistered = sorted(unregistered, key=lambda x: x["hostname"].lower())
    return jsonify(unregistered=unregistered, tags=DEVICE_TAGS)



@api_routes.route('/registered_devices')
@login_required
def api_registered_devices():
    devices = []
    for machine_id, nickname, registered_at, tag in get_registered_devices():
        dt = datetime.fromisoformat(registered_at)
        devices.append({
            "machine_id": machine_id,
            "nickname": nickname,
            "registered_at": dt.strftime("%m/%d/%y %I:%M%p").lstrip("0").replace("/0", "/"),
            "tag": tag
        })
    return jsonify(registered=devices)



# Send the game status kill API


# In-memory fallback for demo; replace with persistent storage or MQTT retained message in production
GAMES_STATUS_DEFAULT = {
    "enable": False,
    "Epic": False,
    "Steam": False,
    "Battle": False,
    "Riot": False
}
# games_status_cache = GAMES_STATUS_DEFAULT.copy()

@api_routes.route('/games_status', methods=['GET'])
@login_required
def get_games_status():
    status = get_esports_status()
    if status is None:
        status = GAMES_STATUS_DEFAULT
    return jsonify(status)

@api_routes.route('/games_status', methods=['POST'])
@login_required
def update_games_status():
    data = request.get_json()
    publish_esports_status(data)
    return jsonify({"success": True})