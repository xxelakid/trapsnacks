# services/kitchen_service.py
# KitchenService - FR 6 Item Availability.

from extensions import db
from models import MenuItem
from services.notifier import Notifier


class KitchenService:
    @staticmethod
    def set_availability(item_id, available):
        item = db.get_or_404(MenuItem, item_id)
        item.available = bool(available)
        db.session.commit()
        Notifier.notify('item_availability_changed', item.to_dict(), 'staff')
        Notifier.notify('item_availability_changed', item.to_dict(), 'chef')
        return item
