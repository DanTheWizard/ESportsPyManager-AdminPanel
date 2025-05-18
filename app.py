from flask import Flask
from flask_login import LoginManager
from routes import app_routes
from api import api_routes
from users import load_user
from database import init_db
from threading import Thread
from src.mqtt_client import mqtt_background_loop
from datetime import datetime
from config import SECRET_KEY

# before app.run(...)
init_db()

# Start MQTT connection in a separate thread
mqtt_thread = Thread(target=mqtt_background_loop)
mqtt_thread.daemon = True
mqtt_thread.start()

app = Flask(__name__)
app.secret_key = SECRET_KEY  # Use os.getenv in production

@app.context_processor
def inject_now():
    return {'now': lambda: datetime.now()}

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
