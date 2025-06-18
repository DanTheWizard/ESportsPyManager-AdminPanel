from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from database import register_device, get_registered_devices, remove_device
from users import validate_login
from src.mqtt_client import connected_devices, hostnames, last_active, device_status
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

@app_routes.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('app_routes.login'))


########################################################################################################################

# Dashboard Section
@app_routes.route('/dashboard')
@login_required
def dashboard():
    from src.mqtt_client import last_active
    now = datetime.now()

    registered = get_registered_devices()
    total = len(registered)
    online = 0
    offline = 0

    for machine_id, *_ in registered:
        last = last_active.get(machine_id)
        if last and (now - last).total_seconds() <= OFFLINE_DEVICE_TIMEOUT:
            online += 1
        else:
            offline += 1

    return render_template(
        "dashboard.html",
        total=total,
        online=online,
        offline=offline,
        user=current_user.id,
        ENABLE_DASH_CHART=ENABLE_DASH_CHART,
        DASH_CHART_REFRESH_TIMEOUT_MS=(DASH_CHART_REFRESH_TIMEOUT * 1000)
    )



########################################################################################################################

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
    for machine_id, nickname, registered_at, last_seen, tag in registered_rows:
        dt = datetime.fromisoformat(registered_at)
        registered.append({
            "machine_id": machine_id,
            "nickname": nickname,
            "registered_at": dt.strftime("%m/%d/%y %I:%M%p").lstrip("0").replace("/0", "/"),
            "tag": tag,
        })

    return render_template(
        "manage_devices.html",
        unregistered=unregistered,
        registered=registered,
        DEVICE_TAGS=DEVICE_TAGS,
        OFFLINE_DEVICE_TIMEOUT=OFFLINE_DEVICE_TIMEOUT,
        REFRESH_TIMEOUT_MS=(OVERVIEW_REFRESH_TIMEOUT*1000)
    )

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

########################################################################################################################

# Overview Section

@app_routes.route('/overview')
@login_required
def overview_page():
    return render_template(
        "overview.html",
        devices=build_device_data(),
        OFFLINE_DEVICE_TIMEOUT=OFFLINE_DEVICE_TIMEOUT,
        REFRESH_TIMEOUT_MS=(OVERVIEW_REFRESH_TIMEOUT*1000)
    )

@app_routes.route('/api/overview_data')
@login_required
def api_overview_data():
    return jsonify(devices=build_device_data())


def build_device_data():
    now = datetime.now()
    registered_rows = get_registered_devices()
    devices = []
    for machine_id, nickname, *_, tag in registered_rows:
        last = last_active.get(machine_id)
        online = bool(last and (now - last).total_seconds() <= OFFLINE_DEVICE_TIMEOUT)
        stats = device_status.get(machine_id, {})
        devices.append({
            "nickname": nickname,
            "tag": tag,
            "cpu": stats.get("cpu", "—"),
            "ram": stats.get("ram", "—"),
            "user": stats.get("user", "—"),
            "app": stats.get("app", "—"),
            "last_active": last.isoformat() if last else None,
            "online": online
        })
    return devices
