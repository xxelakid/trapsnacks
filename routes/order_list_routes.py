# routes/order_list_routes.py
# OrderListRoutes - the cashier's Order List: every pickup and delivery order for a day with
# its status. Ready pickup orders are marked Collected here; delivery orders show the rider
# and the delivery status.

from datetime import datetime, timedelta
from flask import Blueprint, jsonify, render_template, request
from models import Order
from routes.auth_routes import roles_required

order_list_routes = Blueprint('order_list_routes', __name__)


@order_list_routes.get('/order-list')
@roles_required('cashier', 'owner')
def order_list_page():
    return render_template('order_list.html', today=datetime.now().strftime('%Y-%m-%d'))


@order_list_routes.get('/api/orders/list')
@roles_required('cashier', 'owner')
def order_list():
    """All orders placed on one day (today unless ?date=YYYY-MM-DD), every status.
    Pickup orders from EARLIER days that are still waiting to be collected are added too,
    so none are forgotten."""
    try:
        day = datetime.strptime(request.args.get('date', ''), '%Y-%m-%d')
    except ValueError:
        day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    orders = (Order.query.filter(Order.created_at >= day, Order.created_at < day + timedelta(days=1))
              .order_by(Order.created_at.desc()).all())
    waiting = (Order.query.filter(Order.order_type == 'pickup', Order.status == 'Ready',
                                  Order.created_at < day)
               .order_by(Order.created_at).all())
    result = [dict(o.to_dict(), earlier=False) for o in orders]
    result += [dict(o.to_dict(), earlier=True) for o in waiting]
    return jsonify(result)
