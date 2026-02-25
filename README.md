# ESportsPyManager Admin Panel

A Flask-based web admin panel for managing devices and users, integrated with MQTT for real-time device status updates and remote actions. This project is designed to provide a secure and user-friendly interface for managing ESports lab devices and monitoring their status.

> [!Warning]
> 🛠️ This project is under active development and tailored for specific deployment environments.
>
> If you want to use it, **you will have to** modify some parts of it

> [!CAUTION]
> This is my first Flask project, so it may not follow best practices or conventions.


> [!NOTE]  
> ⚙️ This project was made for fun, testing, deploying on my managed computers, and practical experimentation.
> 
> I am sharing the code to help others learn and adapt it for their own use cases 🙂

---

## 📝 TODO:
 - Figure out how to utilise the DynSec plugin of Mosquitto to limit access, to prevent issues if someone extracts a device password from the app

---

## ✨ Features

- 🔐 **User Authentication**
  - Secure login system using Flask-Login.
  
- 🔄 **WebSocket Integration**
  - Background WebSocket client running in a separate thread for real-time communication.
  
- 🗄️ **Database Management**
  - Initializes and manages device status tables.
  
- 🌐 **REST API & Web Routes**
  - Organized routes for API and web interface in separate modules.
  
- 🛠️ **Configurable Settings**
  - Uses environment variables and config files for flexible deployment.

---

## 💻 Client Tool
You can find the client tool to this [here](https://github.com/DanTheWizard/ESportsPyManager):
- https://github.com/DanTheWizard/ESportsPyManager

---

## 📦 Requirements

- Python 3.9 or higher _(Made with 3.13)_
- Dependencies (see `requirements.txt`):
  - `flask`
  - `flask-login`
  - `python-dotenv`
  - `paho-mqtt`
  - `bleach`
  - `gunicorn`

---

## 🚀 Running the Project

### Locally

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set environment variables in a `.env` file or your shell.

3. Run the Flask app with gunicorn:
   ```bash
   gunicorn -t 60 -w 2 -n ESports-PyManager --bind 0.0.0.0:5000 app:app
   ```

### Using Docker

1. Build and start the container:
   ```bash
   docker-compose up --build
   ```

2. The app will be accessible at `http://localhost:8070` or the port you define in `docker-compose.yml`.

---

## 🔧 Docker Configuration

- The service listens on port 5000 inside the container, mapped to 8070 on the host.
- Environment variables can be set in the `.env` file or directly in `docker-compose.yml`.
- Database persistence can be enabled by uncommenting the volume mapping in `docker-compose.yml`.

---

## 🔒 Example `.env`

```ini
SECRET_KEY=your_secret_key_here
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_password

WS_SERVER=your_mqtt_server
WS_USERNAME=your_mqtt_username
WS_PASSWORD=your_mqtt_password
WS_PORT=your_mqtt_port
WS_TLS=True

DEVICE_TAGS=["Room1","Room2","Admin","Test-Bench"]

# Based from PyAppManager (Client Tool)
GAME_LIST=["Epic","Steam","Battle","Riot","MCJava","MCEdu"]
ACTIONS_LIST=["none","test","shutdown","reboot","say","MCEdu","MCJava","ID"]
ACTIONS_WITH_ARGUMENT=["shutdown","say"]

ENABLE_DASH_CHART=True
OFFLINE_DEVICE_TIMEOUT=15
ACTIONS_REFRESH_TIMEOUT=10
OVERVIEW_REFRESH_TIMEOUT=4
DASH_CHART_REFRESH_TIMEOUT=5
CALC_CHART_AVG_TIMEOUT=5

# Supports Decimal (Float)
AVG_PERSIST_MINUTES=2.5
```

