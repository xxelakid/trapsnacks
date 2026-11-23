# services/remove_rider_service.py
# RemoveRiderService - FR 9 Remove a Rider.

from extensions import db
from models import Rider, Delivery, User
from services.notifier import Notifier


class RemoveRiderService:
    @staticmethod
    def remove_rider(rider_id):
        rider = db.get_or_404(Rider, rider_id)
        active = Delivery.query.filter(Delivery.rider_id == rider.id,
                                       Delivery.status.in_(['Accepted', 'Picked up'])).first()
        if active:
            raise ValueError(f'{rider.name} has an active delivery (order #{active.order_id}) '
                             f'and cannot be removed until it is delivered.')
        rider.removed = True               # kept so the delivery history still shows the name
        rider.status = 'unavailable'
        User.query.filter_by(rider_id=rider.id).update({'active': False})   # turns off the rider's login
        db.session.commit()
        Notifier.notify('rider_changed', rider.to_dict(), 'staff')
        return rider
