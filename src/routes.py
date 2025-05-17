from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from database import register_device, get_registered_devices, get_unregistered_devices, remove_device
from users import validate_login
from src.mqtt_client import connected_devices

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


@app_routes.route('/live_devices')
@login_required
def live_devices():
    registered = get_registered_machine_ids()  # machine_ids
    all_live = sorted(connected_devices)

    devices = []
    for machine_id in all_live:
        is_registered = machine_id in registered
        devices.append({
            "machine_id": machine_id,
            "registered": is_registered
        })

    return render_template("live_devices.html", devices=devices)

def get_registered_machine_ids():
    return {device[0] for device in get_registered_devices()}

@app_routes.route('/devices')
@login_required
def device_list():
    registered = get_registered_devices()
    unregistered = get_unregistered_devices()
    return render_template("devices.html", registered=registered, unregistered=unregistered)


@app_routes.route('/register_device', methods=['POST'])
@login_required
def register_device_route():
    data = request.json
    machine_id = data.get("machine_id")
    nickname = data.get("nickname")

    if machine_id and nickname:
        register_device(machine_id, nickname)
        return {"status": "success"}, 200
    else:
        return {"error": "Missing fields"}, 400

@app_routes.route('/register_from_live', methods=['POST'])
@login_required
def register_from_live():
    machine_id = request.form.get("machine_id")
    nickname = request.form.get("nickname")

    if machine_id and nickname:
        register_device(machine_id, nickname)
        flash(f"Device {machine_id} registered as '{nickname}'", "success")
    else:
        flash("Missing fields", "error")

    return redirect(url_for('app_routes.live_devices'))
