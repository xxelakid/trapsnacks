# routes/rider_routes.py
# RiderRoutes - FR 4 Accept a Delivery (rider screen, availability, accept, owner assignment).

from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user
from extensions import db
from models import Delivery, Rider
from routes.auth_routes import roles_required, run_service
from services.request_rider import RequestRider

rider_routes = Blueprint('rider_routes', __name__)


def my_rider():
    return db.get_or_404(Rider, current_user.rider_id)


@rider_routes.get('/rider')
@roles_required('rider')
def rider_page():
    return render_template('rider.html', rider=my_rider())


@rider_routes.get('/api/rider/state')
@roles_required('rider')
def rider_state():
    """Everything the rider screen needs when it loads or reconnects."""
    rider = my_rider()
    current = (Delivery.query.filter(Delivery.rider_id == rider.id,
                                     Delivery.status.in_(['Accepted', 'Picked up'])).first())
    offers = []
    if rider.status == 'available':
        offers = [d.offer_dict() for d in Delivery.query.filter_by(status='Offered')]
    return jsonify(status=rider.status, offers=offers,
                   current=current.full_dict() if current else None)


@rider_routes.post('/api/riders/me/status')
@roles_required('rider')
def set_my_status():
    status = (request.get_json(silent=True) or {}).get('status')
    return run_service(lambda: RequestRider.set_rider_status(current_user.rider_id, status).to_dict())


@rider_routes.post('/api/deliveries/<int:delivery_id>/accept')
@roles_required('rider')
def accept(delivery_id):
    return run_service(lambda: RequestRider.accept_delivery(delivery_id, my_rider()).full_dict())


@rider_routes.get('/api/riders/available')
@roles_required('owner')
def available_riders():
    riders = Rider.query.filter_by(status='available', removed=False).order_by(Rider.name).all()
    return jsonify([rider.to_dict() for rider in riders])


@rider_routes.post('/api/deliveries/<int:delivery_id>/assign')
@roles_required('owner')
def assign(delivery_id):
    rider_id = (request.get_json(silent=True) or {}).get('rider_id')
    return run_service(lambda: RequestRider.assign_manually(delivery_id, int(rider_id or 0)).staff_dict())


@rider_routes.post('/api/riders/<int:rider_id>/status')
@roles_required('owner')
def owner_sets_status(rider_id):
    status = (request.get_json(silent=True) or {}).get('status')
    return run_service(lambda: RequestRider.set_rider_status(rider_id, status).to_dict())
