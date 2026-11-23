# services/order_service.py
# OrderService - FR 0 Create Order (and FR 6 SR-2: unavailable items are refused).

from extensions import db
from models import Order, OrderItem, MenuItem, StatusChange
from services.notifier import Notifier


class OrderService:
    @staticmethod
    def make_items(items):
        """Checks the list of items and turns it into OrderItem objects.
        Also used by EditOrderService so both features follow the same rules."""
        if not items:
            raise ValueError('An order needs at least one item.')
        result = []
        for item in items:
            menu_item = db.session.get(MenuItem, int(item.get('id', 0)))
            if menu_item is None:
                raise ValueError('One of the items does not exist.')
            if not menu_item.available:
                raise ValueError(f'{menu_item.name} is not available right now.')
            quantity = int(item.get('qty', 1))
            if quantity < 1:
                raise ValueError('Quantity must be at least 1.')
            result.append(OrderItem(menu_item_id=menu_item.id, quantity=quantity,
                                    addons=(item.get('addons') or '').strip()))
        return result

    @staticmethod
    def create_order(data, user):
        order_type = data.get('order_type')
        if order_type not in ('pickup', 'delivery'):
            raise ValueError('Choose Pickup or Delivery.')
        if order_type == 'delivery' and not (data.get('address') or '').strip():
            raise ValueError('A delivery order needs an address.')

        order = Order(order_type=order_type,
                      customer_name=(data.get('customer_name') or '').strip(),
                      phone=(data.get('phone') or '').strip(),
                      address=(data.get('address') or '').strip(),
                      special_instructions=(data.get('special_instructions') or '').strip())
        order.items = OrderService.make_items(data.get('items'))
        db.session.add(order)
        db.session.add(StatusChange(order=order, old_status=None, new_status='New', user_id=user.id))
        db.session.commit()                                    # save FIRST ...

        Notifier.notify('order_created', order.to_dict(), 'chef')   # ... then tell the kitchen
        Notifier.notify('order_created', order.to_dict(), 'staff')
        return order
