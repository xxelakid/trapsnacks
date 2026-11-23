# seed.py
# Deletes ALL data and fills the database with demo users, riders and menu items.
# Run it with:  python seed.py

from werkzeug.security import generate_password_hash
from app import create_app
from extensions import db
from models import MenuItem, Rider, User

MENU = [
    # (name, price in JMD, category)
    ('Bacon, Egg & Cheese Sandwich', 850, 'Sandwiches'),
    ('Ham & Cheese Sandwich', 750, 'Sandwiches'),
    ('Turkey Club Sandwich', 950, 'Sandwiches'),
    ('Chicken Wrap', 900, 'Sandwiches'),
    ('Bacon, Egg & Cheese Patty', 550, 'Patties'),
    ('Beef Patty', 350, 'Patties'),
    ('Chicken Patty', 380, 'Patties'),
    ('Vegetable Patty', 330, 'Patties'),
    ('Korean Honey Butter Chips', 650, 'Imported Snacks'),
    ('Japanese Kit Kat (Matcha)', 600, 'Imported Snacks'),
    ('Takis Fuego', 550, 'Imported Snacks'),
    ('Cheese Board for Two', 2500, 'Deli'),
    ('Pastrami (per 1/4 lb)', 1100, 'Deli'),
    ('Fresh Fruit Juice', 450, 'Drinks'),
    ('Iced Coffee', 500, 'Drinks'),
]

STAFF = [
    # (username, password, role)
    ('owner', 'owner123', 'owner'),
    ('cashier1', 'cashier123', 'cashier'),
    ('cashier2', 'cashier123', 'cashier'),
    ('chef1', 'chef123', 'chef'),
    ('chef2', 'chef123', 'chef'),
]

RIDERS = [
    # (name, phone, address, TRN, e-mail, username)
    ('Andre Brown', '876-555-0101', '12 Hope Road, Kingston 6', '123-456-789', 'andre@example.com', 'rider1'),
    ('Kemar Smith', '876-555-0102', '4 Barbican Road, Kingston 8', '234-567-891', 'kemar@example.com', 'rider2'),
    ('Shanice Reid', '876-555-0103', '9 Old Hope Road, Kingston 5', '345-678-912', 'shanice@example.com', 'rider3'),
    ('Damion Clarke', '876-555-0104', '22 Red Hills Road, Kingston 19', '456-789-123', 'damion@example.com', 'rider4'),
]

app = create_app()
with app.app_context():
    db.drop_all()
    db.create_all()

    for name, price, category in MENU:
        db.session.add(MenuItem(name=name, price=price, category=category))

    for username, password, role in STAFF:
        db.session.add(User(username=username, role=role,
                            password_hash=generate_password_hash(password)))

    for name, phone, address, trn, email, username in RIDERS:
        rider = Rider(name=name, phone=phone, address=address, trn=trn, email=email,
                      status='available')
        db.session.add(rider)
        db.session.flush()                       # gives the rider an id
        db.session.add(User(username=username, role='rider', rider_id=rider.id,
                            password_hash=generate_password_hash('rider123')))

    db.session.commit()
    print('Database ready.')
    print('Logins: owner/owner123  cashier1/cashier123  chef1/chef123  rider1..rider4/rider123')
