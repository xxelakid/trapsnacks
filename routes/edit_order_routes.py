# routes/edit_order_routes.py
# EditOrderRoutes - FR 2 Edit Order.

from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user
from extensions import db
from models import Order
from routes.auth_routes import roles_required, run_service
from services.edit_order_service import EditOrderService

edit_order_routes = Blueprint('edit_order_routes', __name__)


@edit_order_routes.get('/orders/<int:order_id>/edit')
@roles_required('cashier', 'owner')
def edit_page(order_id):
    order = db.get_or_404(Order, order_id)
    return render_template('edit_order.html', order=order)


@edit_order_routes.get('/api/orders/<int:order_id>')
@roles_required('cashier', 'owner', 'chef')
def get_order(order_id):
    return jsonify(db.get_or_404(Order, order_id).to_dict())


@edit_order_routes.post('/api/orders/<int:order_id>/edit')
@roles_required('cashier', 'owner')
def edit_order(order_id):
    data = request.get_json(silent=True) or {}
    return run_service(lambda: EditOrderService.edit_order(order_id, data, current_user).to_dict())
