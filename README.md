# TrapSnacks Order & Delivery System

COMP2140 Group THUR_5-7_G05. A Flask web app for TrapSnacks: cashier orders, kitchen display,
riders accepting deliveries, delivery tracking, and rider and staff management.

Live: deployed on Render with a Neon PostgreSQL database (see `RENDER_SETUP.md`).

## Run it on your own laptop

    python -m venv venv
    venv\Scripts\activate          (Mac: source venv/bin/activate)
    pip install -r requirements.txt
    python seed.py                 (LOCAL ONLY: deletes everything and adds demo data)
    python app.py

Open http://127.0.0.1:5000

| Username (local demo data) | Password | Role |
|---|---|---|
| owner | owner123 | Store owner |
| cashier1, cashier2 | cashier123 | Cashier |
| chef1, chef2 | chef123 | Chef |
| rider1 to rider4 | rider123 | Rider |

## Run the tests

    python -m pytest

## Team Members & Responsibilities

| Feature | Member |
|---|---|
| Project foundation, Manage Staff, FR 1 Update Order Status, FR 9 Remove a Rider, required customer details | Orlando (team leader) |
| FR 0 Create Order, FR 6 Item Availability | Brianna |
| FR 2 Edit Order | Jaden |
| FR 3 Cancel Order | Darrin |
| FR 4 Accept a Delivery, FR 7 Add a Rider | Zori |
| FR 5 View Delivery Status, FR 8 Edit a Rider | Anaya |
