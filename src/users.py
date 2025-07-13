from flask_login import UserMixin
from werkzeug.security import check_password_hash
from config import *


USER_DB = {
    f"{ADMIN_USERNAME}": f"{ADMIN_PASSWORD}"
}

class User(UserMixin):
    def __init__(self, username):
        self.id = username

def validate_login(username, password):
    if username in USER_DB and check_password_hash(USER_DB[username], password):
        return User(username)
    return None

def load_user(user_id):
    if user_id in USER_DB:
        return User(user_id)
    return None
