# routes/delivery_display_routes.py
# DeliveryDisplayRoutes - FR 5 View Delivery Status.

from flask import Blueprint, current_app, jsonify, render_template, request
from flask_login import current_user
from extensions import db
from models import Rider
from routes.auth_routes import roles_required, run_service
from services.delivery_service import DeliveryService

delivery_display_routes = Blueprint('delivery_display_routes', __name__)


@delivery_display_routes.get('/deliveries')
@roles_required('cashier', 'owner')
def deliveries_page():
    return render_template('deliveries.html',
                           alert_minutes=current_app.config['NO_RIDER_ALERT_MINUTES'])


@delivery_display_routes.get('/api/deliveries/active')
@roles_required('cashier', 'owner')
def active():
    return jsonify([d.staff_dict() for d in DeliveryService.active_deliveries()])


@delivery_display_routes.get('/api/deliveries/history')
@roles_required('cashier', 'owner')
def history():
    return jsonify([d.staff_dict() for d in DeliveryService.delivery_history()])


@delivery_display_routes.post('/api/deliveries/<int:delivery_id>/status')
@roles_required('rider')
def rider_updates_status(delivery_id):
    status = (request.get_json(silent=True) or {}).get('status')
    rider = db.get_or_404(Rider, current_user.rider_id)
    return run_service(lambda: DeliveryService.update_delivery(delivery_id, status, rider).full_dict())
