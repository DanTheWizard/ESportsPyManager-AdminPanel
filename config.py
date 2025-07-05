from dotenv import load_dotenv                          # User .env file to load confidential data without uploading them to GitHub
from werkzeug.security import generate_password_hash
import os



load_dotenv()                                                # Load the variables from the .env file

# Tags Devices can have
DEVICE_TAGS = ["Stream-OS", "DoeD", "Admin", "Test Bench"]

# List of all available games to kill (MUST HAVE "enable" AS THE FIRST ITEM)
GAME_LIST = ['enable', 'Epic', 'Steam', 'Battle', 'Riot']

# List of all available actions (Must be the ones in PyAppManager)
ACTIONS_LIST = ["none", "test", "shutdown", "say", "MCEdu", "MCJava", "ID"]

# Actions that require an argument (argBox)
ACTIONS_WITH_ARGUMENT = ["shutdown", "say"]


ADMIN_USERNAME   = os.getenv("ADMIN_USERNAME")                              ;"The Admin Username for login"
ADMIN_PASSWORD   = generate_password_hash(os.getenv("ADMIN_PASSWORD"))      ;"Admin Password for Login"
SECRET_KEY       = os.getenv("SECRET_KEY")


WS_SERVER                 = os.getenv("WS_SERVER")          ;"Websocket Server Location"
WS_PORT                   = int(os.getenv("WS_PORT"))       ;"Websocket Port"
WS_USERNAME               = os.getenv("WS_USERNAME")        ;"Websocket Username Authentication"
WS_PASSWORD               = os.getenv("WS_PASSWORD")        ;"Websocket Password Authentication"
WS_USE_TLS                = bool(os.getenv("WS_TLS"))       ;"Whether to use TLS based from the server"

ENABLE_DASH_CHART         = True  ;"Whether to enable the Average calculations for the dashboard chart, and the chart itself on the dashboard"

DEBUG_WS = True

OFFLINE_DEVICE_TIMEOUT     = 15   ;"Time to determine since last device publish to consider it offline (in seconds) [Recommended at least 15]"
ACTIONS_REFRESH_TIMEOUT    = 10   ;"Actions page JavaScript refresh timout (in seconds) of checking whether devices are offline [Recommended at least 10]"
OVERVIEW_REFRESH_TIMEOUT   = 4    ;"Overview page JavaScript refresh timout (in seconds) of the current data [Recommended to be set to the PUBLISH_TIMEOUT]"
DASH_CHART_REFRESH_TIMEOUT = 5    ;"The timeout to refresh the chart with the average CPU and RAM% [Recommended to be the same as CALC_CHART_AVG_TIMEOUT]"
CALC_CHART_AVG_TIMEOUT     = 5    ;"The timeout between calculating the average CPU and RAM [Recommended to be the same as DASH_CHART_REFRESH_TIMEOUT]"

AVG_PERSIST_MINUTES        =2.5   ;"How recent should the persistent data of average values be kept (older than this number will be discarded)"