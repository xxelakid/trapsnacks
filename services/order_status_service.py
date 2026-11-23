# services/order_status_service.py
# OrderStatusService - FR 1 Update Order Status.

from extensions import db
from models import Order, StatusChange
from services.notifier import Notifier

NEXT_STATUS = {'New': 'Preparing', 'Preparing': 'Ready'}   # the only moves allowed


class OrderStatusService:
    @staticmethod
    def change_status(order_id, new_status, user):
        order = db.get_or_404(Order, order_id)
        if NEXT_STATUS.get(order.status) != new_status:
            raise ValueError(f'Order #{order.id} cannot go from {order.status} to {new_status}. '
                             f'Statuses must go New, then Preparing, then Ready.')

        db.session.add(StatusChange(order_id=order.id, old_status=order.status,
                                    new_status=new_status, user_id=user.id))
        order.status = new_status
        db.session.commit()

        update = {'id': order.id, 'status': new_status}
        for room in ('chef', 'staff'):
            Notifier.notify('order_status_changed', update, room)

        return order
