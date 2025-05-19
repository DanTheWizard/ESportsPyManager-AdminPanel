from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from database import register_device, get_registered_devices, remove_device
from users import validate_login
from src.mqtt_client import connected_devices, hostnames, last_active, device_status
from src.mqtt_client import client as mqtt_client
from datetime import datetime
from config import *


api_routes = Blueprint("api_routes", __name__, url_prefix="/api")

@api_routes.route('/dashboard_stats')
@login_required
def api_dashboard_stats():
    from src.mqtt_client import last_active
    now = datetime.now()

    registered = get_registered_devices()
    registered_ids = {r[0] for r in registered}
    total = len(registered)
    online = 0
    unregistered_online = 0

    for machine_id in connected_devices:
        last = last_active.get(machine_id)
        if last and (now - last).total_seconds() <= OFFLINE_DEVICE_TIMEOUT:
            if machine_id in registered_ids:
                online += 1
            else:
                unregistered_online += 1

    return jsonify({
        "total": total,
        "online": online,
        "offline": total - online,
        "unregistered": unregistered_online
    })

@api_routes.route('/device_usage_data')
@login_required
def api_device_usage_data():
    from src.mqtt_client import device_status, last_active
    now = datetime.now()

    usage = []
    for machine_id, nickname, *_ in get_registered_devices():
        last = last_active.get(machine_id)
        if not last or (now - last).total_seconds() > OFFLINE_DEVICE_TIMEOUT:
            continue  # Skip offline

        stats = device_status.get(machine_id, {})
        try:
            cpu = float(stats.get("cpu", 0))
            ram = float(stats.get("ram", 0))
        except ValueError:
            cpu = ram = 0.0

        usage.append({
            "nickname": nickname,
            "cpu": cpu,
            "ram": ram
        })

    return jsonify(devices=usage)

@api_routes.route("/avg_usage_history")
@login_required
def api_avg_usage_history():
    from src.mqtt_client import history_samples
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
    machine_id = request.form.get("machine_id")
    nickname   = request.form.get("nickname")
    tag        = request.form.get("tag")
    print("From:", tag)

    if machine_id and nickname:
        register_device(machine_id, nickname, tag)
        flash(f"Device {machine_id} registered as '{nickname}'", "success")
    else:
        flash("Missing fields", "error")

    return redirect(url_for('app_routes.manage_devices'))

@api_routes.route('/deregister', methods=['POST'])
@login_required
def deregister_device():
    machine_id = request.form.get("machine_id")
    if machine_id:
        remove_device(machine_id)
        flash(f"Device {machine_id} has been removed", "info")
    return redirect(url_for('app_routes.manage_devices'))



# Send Actions to PC

@api_routes.route('/send_action', methods=['POST'])
@login_required
def send_action():
    machine_ids = request.form.getlist('selected_devices')
    action = request.form.get("bulk_action") or "none"
    argument = request.form.get("bulk_argument", "").strip()

    if not machine_ids:
        flash("No devices selected for bulk action.", "warning")
        return redirect(url_for('app_routes.actions_page'))

    final_action = action
    if argument and action in ["shutdown", "say"]:
        final_action = f"{action}:{argument}"

    for machine_id in machine_ids:
        mqtt_client.publish(f"PC/{machine_id}/action", final_action)

    flash(f"Sent '{final_action}' to {len(machine_ids)} device(s).", "success")
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
    statuses = []
    now = datetime.now()
    for machine_id, nickname, *_ in get_registered_devices():
        last = last_active.get(machine_id)
        online = bool(last and (now - last).total_seconds() <= OFFLINE_DEVICE_TIMEOUT)
        statuses.append({
            "machine_id": machine_id,
            "nickname": nickname,
            "online": online,
            "last_active": last.isoformat() if last else None
        })
    return jsonify(statuses=statuses)




