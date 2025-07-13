from dotenv import load_dotenv                          # User .env file to load confidential data without uploading them to GitHub
from werkzeug.security import generate_password_hash
import os
import ast



load_dotenv()                                                # Load the variables from the .env file

# Tags Devices can have
DEVICE_TAGS = ast.literal_eval(os.getenv("DEVICE_TAGS", '["No", "Tags", "Set"]'))

# List of all available games to kill based on the APP_MAP in PyAppManager
# Sets enable to be first, so not needed in the .env file
GAME_LIST = ["enable"] + ast.literal_eval(os.getenv("GAME_LIST", '["No", "Games", "Set"]'))

# List of all available actions (Must be the ones in PyAppManager) from .env file
ACTIONS_LIST = ast.literal_eval(os.getenv("ACTIONS_LIST", '["No", "Actions", "Set"]'))

# Actions that require an argument (argBox) from .env based on PyAppManager
ACTIONS_WITH_ARGUMENT = ast.literal_eval(os.getenv("ACTIONS_WITH_ARGUMENT", '[]'))

ADMIN_USERNAME   = os.getenv("ADMIN_USERNAME")                              ;"The Admin Username for login"
ADMIN_PASSWORD   = generate_password_hash(os.getenv("ADMIN_PASSWORD"))      ;"Admin Password for Login"
SECRET_KEY       = os.getenv("SECRET_KEY")


WS_SERVER                 = os.getenv("WS_SERVER")          ;"Websocket Server Location"
WS_PORT                   = int(os.getenv("WS_PORT"))       ;"Websocket Port"
WS_USERNAME               = os.getenv("WS_USERNAME")        ;"Websocket Username Authentication"
WS_PASSWORD               = os.getenv("WS_PASSWORD")        ;"Websocket Password Authentication"
WS_USE_TLS                = bool(os.getenv("WS_TLS", True)) ;"Whether to use TLS based from the server | Default: True"

ENABLE_DASH_CHART         = bool(os.getenv("ENABLE_DASH_CHART", True))  ;"Whether to enable the Average calculations for the dashboard chart, and the chart itself on the dashboard"

DEBUG_WS = True

OFFLINE_DEVICE_TIMEOUT     = int(os.getenv("OFFLINE_DEVICE_TIMEOUT",      15))    ;"Time to determine since last device publish to consider it offline (in seconds) [Recommended at least 15] | Default: 15"
ACTIONS_REFRESH_TIMEOUT    = int(os.getenv("ACTIONS_REFRESH_TIMEOUT",     10))    ;"Actions page JavaScript refresh timout (in seconds) of checking whether devices are offline [Recommended at least 10] | Default: 10"
OVERVIEW_REFRESH_TIMEOUT   = int(os.getenv("OVERVIEW_REFRESH_TIMEOUT",     4))    ;"Overview page JavaScript refresh timout (in seconds) of the current data [Recommended to be set to the PUBLISH_TIMEOUT] | Default: 4"
DASH_CHART_REFRESH_TIMEOUT = int(os.getenv("DASH_CHART_REFRESH_TIMEOUT",   5))    ;"The timeout to refresh the chart with the average CPU and RAM% [Recommended to be the same as CALC_CHART_AVG_TIMEOUT] | Default: 5"
CALC_CHART_AVG_TIMEOUT     = int(os.getenv("CALC_CHART_AVG_TIMEOUT",       5))    ;"The timeout between calculating the average CPU and RAM [Recommended to be the same as DASH_CHART_REFRESH_TIMEOUT] | Default: 5"

AVG_PERSIST_MINUTES        = float(os.getenv("AVG_PERSIST_MINUTES",      2.5))    ;"How recent should the persistent data of average values be kept (older than this number will be discarded) [Supports decimals] | Default: 2.5"