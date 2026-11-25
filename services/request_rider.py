# services/request_rider.py
# RequestRider - FR 4 Accept a Delivery.
# Offers delivery orders to available riders, lets the FIRST rider accept,
# handles the owner's manual assignment, and keeps rider states up to date.

from datetime import datetime, timedelta
from flask import current_app
from extensions import db
from models import Rider, Delivery
from services.notifier import Notifier


class RequestRider:
    @staticmethod
    def offer_delivery(order):
        """FR 4 SR-2: send an offer to every available rider.
        This happens when the chef starts preparing, so the meal preparation countdown
        (PREP_MINUTES) starts now. Riders, the kitchen and staff all count down to it."""
        now = datetime.now()
        delivery = Delivery(order_id=order.id, status='Offered', offered_at=now,
                            pickup_deadline=now + timedelta(minutes=current_app.config['PREP_MINUTES']))
        db.session.add(delivery)
        db.session.commit()
        for rider in Rider.query.filter_by(status='available', removed=False):
            Notifier.notify('delivery_offer', delivery.offer_dict(), f'rider_{rider.id}')
        Notifier.notify('delivery_changed', delivery.staff_dict(), 'staff')
        return delivery

    @staticmethod
    def accept_delivery(delivery_id, rider):
        """FR 4 SR-3: the first rider to accept gets the delivery."""
        if rider.status != 'available':
            raise ValueError('You must be available (and not on another delivery) to accept.')
        now = datetime.now()

        # This UPDATE only changes the row while it is still "Offered".
        # If two riders tap Accept at the same moment, only the first one changes it.
        taken = Delivery.query.filter_by(id=delivery_id, status='Offered').update(
            {'status': 'Accepted', 'rider_id': rider.id, 'accepted_at': now})
        # (pickup_deadline is NOT changed: the countdown started when the chef began preparing)
        if taken == 0:
            db.session.rollback()
            raise ValueError('Sorry, this delivery has already been taken.')
        rider.status = 'reserved'
        db.session.commit()

        delivery = db.session.get(Delivery, delivery_id)
        Notifier.notify('delivery_assigned', delivery.full_dict(), f'rider_{rider.id}')
        Notifier.notify('offer_closed', {'id': delivery.id}, 'rider')     # remove from other riders
        Notifier.notify('delivery_changed', delivery.staff_dict(), 'staff')
        Notifier.notify('rider_changed', rider.to_dict(), 'staff')
        return delivery

    @staticmethod
    def assign_manually(delivery_id, rider_id):
        """FR 4 SR-5: the store owner assigns or reassigns a delivery."""
        delivery = db.get_or_404(Delivery, delivery_id)
        new_rider = db.get_or_404(Rider, rider_id)
        if delivery.status not in ('Offered', 'Accepted'):
            raise ValueError('This delivery can no longer be reassigned.')
        if new_rider.removed or new_rider.status != 'available':
            raise ValueError('Choose a rider who is available.')

        old_rider = delivery.rider
        now = datetime.now()
        delivery.rider = new_rider
        delivery.status = 'Accepted'
        delivery.accepted_at = now                 # the preparation countdown keeps running
        new_rider.status = 'reserved'
        db.session.commit()

        Notifier.notify('delivery_assigned', delivery.full_dict(), f'rider_{new_rider.id}')
        Notifier.notify('offer_closed', {'id': delivery.id}, 'rider')
        if old_rider:
            Notifier.notify('delivery_removed', {'id': delivery.id, 'order_id': delivery.order_id},
                            f'rider_{old_rider.id}')
            RequestRider.release_rider(old_rider)
        Notifier.notify('delivery_changed', delivery.staff_dict(), 'staff')
        Notifier.notify('rider_changed', new_rider.to_dict(), 'staff')
        return delivery

    @staticmethod
    def set_rider_status(rider_id, status):
        """FR 4 SR-1: a rider (or the owner) switches between available and unavailable."""
        rider = db.get_or_404(Rider, rider_id)
        if status not in ('available', 'unavailable'):
            raise ValueError('Status must be available or unavailable.')
        if rider.status == 'reserved':
            raise ValueError('Finish your current delivery first.')
        rider.status = status
        db.session.commit()
        if status == 'available':
            RequestRider._send_open_offers(rider)
        Notifier.notify('rider_changed', rider.to_dict(), 'staff')
        return rider

    @staticmethod
    def release_rider(rider):
        """Sets a rider back to available after a delivery is delivered, cancelled or moved."""
        if rider.removed:
            return
        rider.status = 'available'
        db.session.commit()
        RequestRider._send_open_offers(rider)
        Notifier.notify('rider_changed', rider.to_dict(), 'staff')

    @staticmethod
    def _send_open_offers(rider):
        """Helper: a rider who has just become available sees offers nobody has taken yet."""
        for delivery in Delivery.query.filter_by(status='Offered'):
            Notifier.notify('delivery_offer', delivery.offer_dict(), f'rider_{rider.id}')
