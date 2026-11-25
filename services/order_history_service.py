# services/order_history_service.py
# OrderHistoryService - Order History (owner only).
# Lists every FINISHED order so the owner can look back at past business:
#   Delivered  - a delivery order the rider marked Delivered
#   Pickup     - a pickup order the kitchen marked Ready (the final step for pickup orders)
#   Cancelled  - any order that was cancelled, with the reason
# Orders still in progress (New, Preparing, or a delivery still on the road) are not listed.

from datetime import datetime, timedelta
from sqlalchemy import and_, or_
from extensions import db
from models import Delivery, Order

OUTCOMES = {
    'delivered': 'Delivered',
    'pickup': 'Picked up (pickup order)',
    'cancelled': 'Cancelled',
}
PER_PAGE = 50


def _conditions():
    """One SQL condition per outcome, so the filters and the counts use the same rules."""
    return {
        'delivered': and_(Order.order_type == 'delivery', Delivery.status == 'Delivered'),
        'pickup': and_(Order.order_type == 'pickup', Order.status == 'Ready'),
        'cancelled': Order.status == 'Cancelled',
    }


def outcome_of(order):
    if order.status == 'Cancelled':
        return 'cancelled'
    if order.order_type == 'pickup':
        return 'pickup'
    return 'delivered'


def order_total(order):
    """Order value at the CURRENT menu prices (prices are not saved on each order)."""
    return sum(item.menu_item.price * item.quantity for item in order.items)


def finished_at(order):
    """When the order reached its final state."""
    if order.status == 'Cancelled' or order.order_type == 'pickup':
        final = [c for c in order.changes if c.new_status == order.status]
        return final[-1].changed_at if final else None
    return order.delivery.delivered_at if order.delivery else None


def _parse_date(text):
    try:
        return datetime.strptime(text, '%Y-%m-%d') if text else None
    except ValueError:
        return None


class OrderHistoryService:
    @staticmethod
    def read_filters(args):
        """Turns the filter form (query string) into clean values."""
        outcome = args.get('outcome', 'all')
        return {
            'outcome': outcome if outcome in OUTCOMES else 'all',
            'date_from': args.get('date_from', '') if _parse_date(args.get('date_from')) else '',
            'date_to': args.get('date_to', '') if _parse_date(args.get('date_to')) else '',
            'q': (args.get('q') or '').strip(),
        }

    @staticmethod
    def _query(filters, outcome=None):
        conditions = _conditions()
        query = Order.query.outerjoin(Delivery, Delivery.order_id == Order.id)
        outcome = outcome or filters['outcome']
        if outcome in conditions:
            query = query.filter(conditions[outcome])
        else:
            query = query.filter(or_(*conditions.values()))

        start, end = _parse_date(filters['date_from']), _parse_date(filters['date_to'])
        if start:
            query = query.filter(Order.created_at >= start)
        if end:
            query = query.filter(Order.created_at < end + timedelta(days=1))   # include that whole day

        q = filters['q']
        if q:
            text = f'%{q}%'
            match = [Order.customer_name.ilike(text), Order.phone.ilike(text)]
            if q.lstrip('#').isdigit():
                match.append(Order.id == int(q.lstrip('#')))
            query = query.filter(or_(*match))
        return query

    @staticmethod
    def search(filters, page=1):
        """One page of finished orders (newest first), plus a summary of ALL matching orders."""
        query = OrderHistoryService._query(filters)
        total_count = query.count()
        pages = max(1, -(-total_count // PER_PAGE))
        page = min(max(1, page), pages)
        orders = (query.order_by(Order.created_at.desc(), Order.id.desc())
                  .offset((page - 1) * PER_PAGE).limit(PER_PAGE).all())

        # The summary ignores the outcome filter so the owner always sees all three counts.
        summary = {}
        for key in OUTCOMES:
            matching = OrderHistoryService._query(filters, outcome=key).all()
            summary[key] = {'count': len(matching),
                            'sales': sum(order_total(o) for o in matching)}
        return {'orders': orders, 'page': page, 'pages': pages,
                'total_count': total_count, 'summary': summary}

    @staticmethod
    def all_matching(filters):
        """Every matching order (for the CSV download)."""
        return OrderHistoryService._query(filters).order_by(Order.created_at.desc(), Order.id.desc()).all()
