# services/cancel_order_service.py
# CancelOrderService - FR 3 Cancel Order.

from extensions import db
from models import Order, StatusChange
from services.notifier import Notifier
from services.request_rider import RequestRider

REASONS = ['Customer changed their mind', 'Duplicate order', 'Item not available',
           'Customer did not pay', 'Other']


class CancelOrderService:
    @staticmethod
    def cancel_order(order_id, reason, user):
        order = db.get_or_404(Order, order_id)
        if order.status not in ('New', 'Preparing'):
            raise ValueError('Only orders that are New or Preparing can be cancelled.')
        if reason not in REASONS:
            raise ValueError('Choose a reason for cancelling.')

        db.session.add(StatusChange(order_id=order.id, old_status=order.status,
                                    new_status='Cancelled', user_id=user.id))
        order.status = 'Cancelled'
        order.cancel_reason = reason

        delivery, rider = order.delivery, None
        if delivery and delivery.status in ('Offered', 'Accepted'):
            rider = delivery.rider
            delivery.status = 'Cancelled'
        db.session.commit()

        Notifier.notify('order_cancelled', {'id': order.id, 'reason': reason}, 'chef')
        Notifier.notify('order_cancelled', {'id': order.id, 'reason': reason}, 'staff')
        if delivery:
            Notifier.notify('offer_closed', {'id': delivery.id}, 'rider')     # withdraw the offer
            Notifier.notify('delivery_changed', delivery.staff_dict(), 'staff')
        if rider:
            Notifier.notify('delivery_cancelled', {'id': delivery.id, 'order_id': order.id},
                            f'rider_{rider.id}')
            RequestRider.release_rider(rider)
        return order
