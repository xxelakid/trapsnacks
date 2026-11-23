# services/staff_service.py
# StaffService - Manage Staff: the owner adds, edits and removes chef and cashier logins.

from werkzeug.security import generate_password_hash
from extensions import db
from models import User

STAFF_ROLES = ('cashier', 'chef')     # the owner and riders are managed elsewhere
MIN_PASSWORD_LENGTH = 8


class StaffService:
    @staticmethod
    def list_staff():
        return (User.query.filter(User.role.in_(STAFF_ROLES), User.active.is_(True))
                .order_by(User.role, User.username).all())

    @staticmethod
    def _check(data, user_id=None, password_required=True):
        """The rules for a staff account. All problems are listed in one message."""
        problems = []
        username = (data.get('username') or '').strip()
        role = data.get('role')
        password = data.get('password') or ''
        if not username:
            problems.append('a username')
        elif ' ' in username:
            problems.append('a username without spaces')
        else:
            taken = User.query.filter_by(username=username).first()
            if taken and taken.id != user_id:
                problems.append('a different username (that one is already used)')
        if role not in STAFF_ROLES:
            problems.append('the role (Cashier or Chef)')
        if (password_required or password) and len(password) < MIN_PASSWORD_LENGTH:
            problems.append(f'a password of at least {MIN_PASSWORD_LENGTH} characters')
        if problems:
            raise ValueError('Please give: ' + ', '.join(problems) + '.')
        return username, role, password

    @staticmethod
    def add_staff(data):
        username, role, password = StaffService._check(data)
        user = User(username=username, role=role, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def get_staff(user_id):
        user = db.get_or_404(User, user_id)
        if user.role not in STAFF_ROLES or not user.active:
            raise ValueError('That account is not a current cashier or chef.')
        return user

    @staticmethod
    def edit_staff(user_id, data):
        """Change the username and role. The password only changes if a new one is typed."""
        user = StaffService.get_staff(user_id)
        username, role, password = StaffService._check(data, user_id=user.id, password_required=False)
        user.username = username
        user.role = role
        if password:
            user.password_hash = generate_password_hash(password)
        db.session.commit()
        return user

    @staticmethod
    def remove_staff(user_id):
        """Switches the account off instead of deleting it: the order history (StatusChange)
        still points to this person, so the database would refuse a delete. A removed
        account cannot log in, and anyone using it is logged out on their next click."""
        user = StaffService.get_staff(user_id)
        user.active = False
        db.session.commit()
        return user
