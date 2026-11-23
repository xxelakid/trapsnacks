# routes/order_routes.py
# OrderRoutes - FR 0 Create Order (also gives the cashier screen its data).

from datetime import datetime
from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user
from models import MenuItem, Order
from routes.auth_routes import roles_required, run_service
from services.order_service import OrderService

order_routes = Blueprint('order_routes', __name__)


@order_routes.get('/cashier')
@roles_required('cashier', 'owner')
def cashier_page():
    return render_template('cashier.html')


@order_routes.get('/api/menu')
@roles_required('cashier', 'owner', 'chef')
def menu():
    items = MenuItem.query.order_by(MenuItem.category, MenuItem.name).all()
    return jsonify([item.to_dict() for item in items])


@order_routes.get('/api/orders/active')
@roles_required('cashier', 'owner', 'chef')
def active_orders():
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    orders = (Order.query.filter(Order.status.in_(['New', 'Preparing', 'Ready']),
                                 Order.created_at >= today)
              .order_by(Order.created_at).all())
    return jsonify([order.to_dict() for order in orders])


@order_routes.post('/api/orders')
@roles_required('cashier', 'owner')
def create_order():
    data = request.get_json(silent=True) or {}
    return run_service(lambda: OrderService.create_order(data, current_user).to_dict(), 201)
