from flask import Flask
from flask_login import LoginManager
from threading import Thread
from datetime import datetime
from src.routes import app_routes
from src.api import api_routes
from src.users import load_user
from src.database import init_db,init_device_status_table
from src.mqtt_client import mqtt_background_loop
from config import SECRET_KEY

PANEL_VERSION="2.2.1"

# before app.run(...)
init_db()
init_device_status_table()

# Start MQTT connection in a separate thread
mqtt_thread = Thread(target=mqtt_background_loop)
mqtt_thread.daemon = True
mqtt_thread.start()

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

@app.context_processor
def inject_now():
    return {'now': lambda: datetime.now()}

@app.context_processor
def inject_appVer():
    return {'PANEL_VERSION': PANEL_VERSION}

# Flask-Login Setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'app_routes.login'

@login_manager.user_loader
def user_loader(user_id):
    return load_user(user_id)

# Register routes from a separate file
app.register_blueprint(app_routes)
app.register_blueprint(api_routes)

if __name__ == '__main__':
    app.run(debug=True)
