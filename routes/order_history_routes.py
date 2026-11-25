# routes/order_history_routes.py
# OrderHistoryRoutes - Order History (owner only): every delivered, picked-up and
# cancelled order, with filters, a summary, and a CSV download.

import csv
import io

from flask import Blueprint, Response, render_template, request
from routes.auth_routes import roles_required
from services.order_history_service import (OUTCOMES, OrderHistoryService, finished_at,
                                            order_total, outcome_of)

order_history_routes = Blueprint('order_history_routes', __name__)


@order_history_routes.get('/history')
@roles_required('owner')
def history_page():
    filters = OrderHistoryService.read_filters(request.args)
    page = request.args.get('page', 1, type=int)
    result = OrderHistoryService.search(filters, page)
    return render_template('order_history.html', filters=filters, outcomes=OUTCOMES,
                           outcome_of=outcome_of, order_total=order_total,
                           finished_at=finished_at, **result)


@order_history_routes.get('/history.csv')
@roles_required('owner')
def history_csv():
    filters = OrderHistoryService.read_filters(request.args)
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(['Order', 'Outcome', 'Type', 'Ordered at', 'Finished at', 'Customer', 'Phone',
                     'Address', 'Items', 'Total (JMD)', 'Rider', 'Cancel reason'])
    for order in OrderHistoryService.all_matching(filters):
        done = finished_at(order)
        writer.writerow([
            order.id, OUTCOMES[outcome_of(order)], order.order_type,
            order.created_at.strftime('%Y-%m-%d %H:%M') if order.created_at else '',
            done.strftime('%Y-%m-%d %H:%M') if done else '',
            order.customer_name, order.phone, order.address,
            '; '.join(f'{i.quantity} x {i.menu_item.name}' + (f' ({i.addons})' if i.addons else '')
                      for i in order.items),
            f'{order_total(order):.2f}',
            order.delivery.rider.name if order.delivery and order.delivery.rider else '',
            order.cancel_reason or '',
        ])
    return Response(out.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=order_history.csv'})
