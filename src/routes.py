from flask           import Blueprint, render_template, redirect, url_for, request, jsonify, flash
from flask_login     import login_user, logout_user, login_required, current_user
from src.database    import get_registered_devices, get_all_device_status, get_online_devices
from src.users       import validate_login
from datetime        import datetime
from config          import *

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
            flash('Invalid credentials')
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
    registered = get_registered_devices()
    registered_ids = {row[0] for row in registered}
    online_ids = get_online_devices()

    total = len(registered)
    online = len(online_ids & registered_ids)
    offline = total - online

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
    online_ids = get_online_devices()

    # Unregistered = online but not in DB - Sorted by Hostname
    status_map = {
        row[0]: row[1]  # machine_id -> hostname
        for row in get_all_device_status()
    }

    unsorted = [
        {
            "machine_id": machine_id,
            "hostname": status_map.get(machine_id, "Unknown")
        }
        for machine_id in (online_ids - registered_ids)
    ]
    unregistered = sorted(unsorted, key=lambda x: x["hostname"].lower())

    # Registered = in DB (some may be offline) - Sorted by Nickname
    registered = []
    for machine_id, nickname, registered_at, tag in registered_rows:
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
        ACTIONS_LIST=ACTIONS_LIST,
        ACTIONS_WITH_ARGUMENT=ACTIONS_WITH_ARGUMENT,
        OFFLINE_DEVICE_TIMEOUT=OFFLINE_DEVICE_TIMEOUT,
        REFRESH_TIMEOUT_MS=(ACTIONS_REFRESH_TIMEOUT * 1000)
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
    online_ids = get_online_devices()
    status_map = {
        row[0]: row  # machine_id -> full row
        for row in get_all_device_status()
    }

    devices = []
    for machine_id, nickname, *_ , tag in registered_rows:
        row = status_map.get(machine_id)
        if row:
            _, _, cpu, ram, user, app, _, last_seen = row
            last_seen_dt = datetime.fromisoformat(last_seen) if last_seen else None
        else:
            cpu = ram = user = app = "—"
            last_seen_dt = None

        online = machine_id in online_ids

        devices.append({
            "nickname": nickname,
            "tag": tag,
            "cpu": cpu or "—",
            "ram": ram or "—",
            "user": user or "—",
            "app": app or "—",
            "last_active": last_seen_dt.isoformat() if last_seen_dt else None,
            "online": online
        })

    return devices
########################################################################################################################

@app_routes.route('/manage-games')
@login_required
def manage_games():
    return render_template(
        'manage_games.html',
        gameList=GAME_LIST
    )
