# FR 2 Edit Order
import pytest
from conftest import delivery_data
from services.edit_order_service import EditOrderService
from services.order_service import OrderService
from services.order_status_service import OrderStatusService


def test_fr2_edit_keeps_order_number_and_marks_edited(cashier, patty, juice):
    order = OrderService.create_order(delivery_data(patty.id), cashier)
    EditOrderService.edit_order(order.id, {'items': [{'id': juice.id, 'qty': 2}],
                                           'address': '5 Hope Road'}, cashier)
    assert order.edited is True
    assert order.items[0].menu_item_id == juice.id


def test_fr2_ready_order_cannot_be_edited(cashier, chef, patty):
    order = OrderService.create_order(delivery_data(patty.id), cashier)
    OrderStatusService.change_status(order.id, 'Preparing', chef)
    OrderStatusService.change_status(order.id, 'Ready', chef)
    with pytest.raises(ValueError):
        EditOrderService.edit_order(order.id, {'items': [{'id': patty.id}], 'address': 'x'}, cashier)


def test_fr2_edit_cannot_remove_every_item(cashier, patty):
    order = OrderService.create_order(delivery_data(patty.id), cashier)
    with pytest.raises(ValueError):
        EditOrderService.edit_order(order.id, {'items': [], 'address': 'x'}, cashier)
