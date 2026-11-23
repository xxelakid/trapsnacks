# services/notifier.py
# Notifier: the ONE place that sends live updates to the screens (Flask-SocketIO).
# A "room" is a group of screens: 'cashier', 'chef', 'owner', 'rider', 'staff' or 'rider_<id>'.

from extensions import socketio


class Notifier:
    @staticmethod
    def notify(event, data, room):
        socketio.emit(event, data, to=room)
