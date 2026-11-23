# extensions.py
# Creates the helper objects once, so every other file can import the same ones.

from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_login import LoginManager
from flask_wtf import CSRFProtect

db = SQLAlchemy()                            # talks to the SQLite database
socketio = SocketIO(async_mode='threading')  # sends live updates to the screens
login_manager = LoginManager()               # remembers who is logged in
csrf = CSRFProtect()                         # blocks forged form submissions
