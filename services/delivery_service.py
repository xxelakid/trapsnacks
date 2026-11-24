# services/delivery_service.py
# DeliveryService - FR 5 View Delivery Status.

from datetime import datetime
from extensions import db
from models import Delivery
from services.notifier import Notifier
from services.request_rider import RequestRider

NEXT_STATUS = {'Accepted': 'Picked up', 'Picked up': 'Delivered'}


class DeliveryService:
    @staticmethod
    def update_delivery(delivery_id, status, rider):
        delivery = db.get_or_404(Delivery, delivery_id)
        if delivery.rider_id != rider.id:
            raise ValueError('This is not your delivery.')
        if NEXT_STATUS.get(delivery.status) != status:
            raise ValueError(f'A delivery cannot go from {delivery.status} to {status}.')
        if status == 'Picked up' and delivery.order.status != 'Ready':
            raise ValueError('The food is not ready yet. Wait until the kitchen marks it Ready.')

        delivery.status = status
        if status == 'Picked up':
            delivery.picked_up_at = datetime.now()
        else:
            delivery.delivered_at = datetime.now()
        db.session.commit()

        Notifier.notify('delivery_changed', delivery.staff_dict(), 'staff')
        if status == 'Delivered':
            RequestRider.release_rider(rider)
        return delivery

    @staticmethod
    def active_deliveries():
        return (Delivery.query.filter(Delivery.status.in_(['Offered', 'Accepted', 'Picked up']))
                .order_by(Delivery.offered_at).all())

    @staticmethod
    def delivery_history():
        return (Delivery.query.filter_by(status='Delivered')
                .order_by(Delivery.delivered_at.desc()).all())
