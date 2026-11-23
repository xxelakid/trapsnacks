# routes/order_status_routes.py
# OrderStatusRoutes - FR 1 Update Order Status (and shows the KitchenDisplayScreen).

from flask import Blueprint, render_template, request
from flask_login import current_user
from routes.auth_routes import roles_required, run_service
from services.order_status_service import OrderStatusService

order_status_routes = Blueprint('order_status_routes', __name__)


@order_status_routes.get('/kitchen')
@roles_required('chef', 'owner')
def kitchen_page():
    return render_template('kitchen.html')


@order_status_routes.post('/api/orders/<int:order_id>/status')
@roles_required('chef', 'owner')
def change_status(order_id):
    new_status = (request.get_json(silent=True) or {}).get('status')
    return run_service(lambda: OrderStatusService.change_status(order_id, new_status,
                                                                current_user).to_dict())
