# routes/cancel_order_routes.py
# CancelOrderRoutes - FR 3 Cancel Order.

from flask import Blueprint, render_template, request
from flask_login import current_user
from extensions import db
from models import Order
from routes.auth_routes import roles_required, run_service
from services.cancel_order_service import CancelOrderService, REASONS

cancel_order_routes = Blueprint('cancel_order_routes', __name__)


@cancel_order_routes.get('/orders/<int:order_id>/cancel')
@roles_required('cashier', 'owner')
def cancel_page(order_id):
    order = db.get_or_404(Order, order_id)
    return render_template('cancel_order.html', order=order, reasons=REASONS)


@cancel_order_routes.post('/api/orders/<int:order_id>/cancel')
@roles_required('cashier', 'owner')
def cancel_order(order_id):
    reason = (request.get_json(silent=True) or {}).get('reason')
    return run_service(lambda: CancelOrderService.cancel_order(order_id, reason,
                                                               current_user).to_dict())
