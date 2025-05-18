from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from database import register_device, get_registered_devices, remove_device
from users import validate_login
from src.mqtt_client import connected_devices, hostnames, last_active
from src.mqtt_client import client as mqtt_client
from datetime import datetime
from config import *

app_routes = Blueprint("app_routes", __name__)

@app_routes.route('/')
def home():
    return redirect(url_for('app_routes.login'))

@app_routes.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = validate_login(username, password)

        if user:
            login_user(user)
            return redirect(url_for('app_routes.dashboard'))
        else:
            flash('Invalid credentials', 'error')
    return render_template('login.html')


@app_routes.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user.id)


@app_routes.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('app_routes.login'))


@app_routes.route('/manage-devices')
@login_required
def manage_devices():
    registered_rows = get_registered_devices()
    registered_ids = {device[0] for device in registered_rows}
    online_ids = connected_devices

    # Unregistered = online but not in DB - Sorted by Hostname
    unsorted = [
        {
            "machine_id": machine_id,
            "hostname": hostnames.get(machine_id, "Unknown")
        }
        for machine_id in (online_ids - registered_ids)
    ]
    unregistered = sorted(unsorted, key=lambda x: x["hostname"].lower())

    # Registered = in DB (some may be offline) - Sorted by Nickname
    registered = []
    for machine_id, nickname, registered_at, last_seen in registered_rows:
        dt = datetime.fromisoformat(registered_at)
        registered.append({
            "machine_id": machine_id,
            "nickname": nickname,
            "registered_at": dt.strftime("%m/%d/%y %I:%M%p").lstrip("0").replace("/0", "/"),
        })

    return render_template("manage_devices.html", unregistered=unregistered, registered=registered)

@app_routes.route('/api/register_from_manage', methods=['POST'])
@login_required
def register_from_manage():
    machine_id = request.form.get("machine_id")
    nickname = request.form.get("nickname")

    if machine_id and nickname:
        register_device(machine_id, nickname)
        flash(f"Device {machine_id} registered as '{nickname}'", "success")
    else:
        flash("Missing fields", "error")

    return redirect(url_for('app_routes.manage_devices'))

@app_routes.route('/api/deregister', methods=['POST'])
@login_required
def deregister_device():
    machine_id = request.form.get("machine_id")
    if machine_id:
        remove_device(machine_id)
        flash(f"Device {machine_id} has been removed", "info")
    return redirect(url_for('app_routes.manage_devices'))


########################################################################################################################

# ACTIONS SECTION
@app_routes.route('/actions')
@login_required
def actions_page():
    devices = get_registered_devices()
    devices = sorted(devices, key=lambda d: d[1].lower())  # Sort by nickname
    return render_template(
        "actions.html",
        devices=devices,
        OFFLINE_DEVICE_TIMEOUT=OFFLINE_DEVICE_TIMEOUT,
        REFRESH_TIMEOUT_MS=(ACTIONS_REFRESH_TIMEOUT*1000)
    )

@app_routes.route('/api/send_action', methods=['POST'])
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



@app_routes.route('/api/send_action_device', methods=['POST'])
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


@app_routes.route('/api/device_statuses')
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
