# services/order_status_service.py
# OrderStatusService - FR 1 Update Order Status.
# A delivery order marked "Preparing" is offered to riders (FR 4).

from extensions import db
from models import Order, StatusChange
from services.notifier import Notifier
from services.request_rider import RequestRider

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

        if order.order_type == 'delivery':
            if new_status == 'Preparing':
                RequestRider.offer_delivery(order)                 # FR 4 starts here
            elif new_status == 'Ready' and order.delivery and order.delivery.rider_id:
                Notifier.notify('order_ready_for_pickup', {'order_id': order.id},
                                f'rider_{order.delivery.rider_id}')
                Notifier.notify('delivery_changed', order.delivery.staff_dict(), 'staff')
        return order

    @staticmethod
    def mark_collected(order_id, user):
        """The cashier hands a Ready PICKUP order to the customer: Ready -> Collected.
        (Delivery orders finish when the rider marks them Delivered instead.)"""
        order = db.get_or_404(Order, order_id)
        if order.order_type != 'pickup':
            raise ValueError(f'Order #{order.id} is a delivery. The rider marks it Delivered.')
        if order.status != 'Ready':
            raise ValueError(f'Order #{order.id} is {order.status}. Only Ready pickup orders can be collected.')

        db.session.add(StatusChange(order_id=order.id, old_status=order.status,
                                    new_status='Collected', user_id=user.id))
        order.status = 'Collected'
        db.session.commit()

        update = {'id': order.id, 'status': 'Collected'}
        for room in ('chef', 'staff'):
            Notifier.notify('order_status_changed', update, room)
        return order
