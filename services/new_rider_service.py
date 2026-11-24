# services/new_rider_service.py
# NewRiderService - FR 7 Add a Rider.

from werkzeug.security import generate_password_hash
from extensions import db
from models import Rider, User

FIELDS = [('name', 'Name'), ('phone', 'Phone number'), ('address', 'Permanent address'),
          ('trn', 'TRN'), ('email', 'E-mail address')]


class NewRiderService:
    @staticmethod
    def validate_rider(data):
        """FR 7 SR-2 and FR 8 SR-2: every field must be filled in."""
        missing = [label for key, label in FIELDS if not (data.get(key) or '').strip()]
        if missing:
            raise ValueError('Please fill in: ' + ', '.join(missing))

    @staticmethod
    def add_rider(data):
        NewRiderService.validate_rider(data)
        username = (data.get('username') or '').strip()
        password = data.get('password') or ''
        if not username or len(password) < 6:
            raise ValueError('Give the rider a username and a password of at least 6 characters.')
        if User.query.filter_by(username=username).first():
            raise ValueError('That username is already taken.')

        rider = Rider(**{key: data[key].strip() for key, _ in FIELDS})
        db.session.add(rider)
        db.session.flush()                    # gives the rider its unique id (FR 7 SR-3)
        db.session.add(User(username=username, role='rider', rider_id=rider.id,
                            password_hash=generate_password_hash(password)))
        db.session.commit()
        return rider
