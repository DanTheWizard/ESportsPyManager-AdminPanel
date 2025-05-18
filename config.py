from dotenv import load_dotenv                          # User .env file to load confidential data without uploading them to GitHub
from werkzeug.security import generate_password_hash
import os



load_dotenv()                                                # Load the variables from the .env file


ADMIN_USERNAME   = os.getenv("ADMIN_USERNAME")                              # The Admin Username for login
ADMIN_PASSWORD   = generate_password_hash(os.getenv("ADMIN_PASSWORD"))      # Admin Password for Login
SECRET_KEY       = os.getenv("SECRET_KEY")


WS_SERVER                 = os.getenv("WS_SERVER")           # Websocket Server Location
WS_PORT                   = int(os.getenv("WS_PORT"))        # Websocket Port
WS_USERNAME               = os.getenv("WS_USERNAME")         # Websocket Username Authentication
WS_PASSWORD               = os.getenv("WS_PASSWORD")         # Websocket Password Authentication
WS_USE_TLS                = bool(os.getenv("WS_TLS"))        # Whether to use TLS based from the server


DEBUG_WS = True

OFFLINE_DEVICE_TIMEOUT    = 15  # Time to determine since last device publish to consider it offline (in seconds) [Recommended at least 15]
ACTIONS_REFRESH_TIMEOUT   = 10   # Actions page JavaScript refresh timout (in seconds) [Recommended at least 10]