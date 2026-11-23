# services/edit_order_service.py
# EditOrderService - FR 2 Edit Order.

from extensions import db
from models import Order, Rider
from services.notifier import Notifier
from services.order_service import OrderService


class EditOrderService:
    @staticmethod
    def edit_order(order_id, data, user):
        order = db.get_or_404(Order, order_id)
        if order.status not in ('New', 'Preparing'):
            raise ValueError('Only orders that are New or Preparing can be edited.')

        new_items = OrderService.make_items(data.get('items'))      # same checks as FR 0
        if order.order_type == 'delivery':
            address = (data.get('address') or '').strip()
            if not address:
                raise ValueError('A delivery order needs an address.')
            order.address = address
        order.items = new_items
        order.special_instructions = (data.get('special_instructions') or '').strip()
        order.edited = True
        db.session.commit()

        Notifier.notify('order_edited', order.to_dict(), 'chef')
        Notifier.notify('order_edited', order.to_dict(), 'staff')

        delivery = order.delivery
        if delivery and delivery.status == 'Accepted':              # FR 2 SR-3
            Notifier.notify('delivery_updated', delivery.full_dict(), f'rider_{delivery.rider_id}')
            Notifier.notify('staff_alert', {'message': f'Order #{order.id} was edited. '
                                                       f'Rider {delivery.rider.name} has the new details.'},
                            'staff')
        elif delivery and delivery.status == 'Offered':              # update the open offer
            for rider in Rider.query.filter_by(status='available', removed=False):
                Notifier.notify('delivery_offer', delivery.offer_dict(), f'rider_{rider.id}')
        return order
