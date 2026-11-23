// static/edit_order.js
// EditOrderScreen: change an order that is New or Preparing (FR 2).

const orderId = document.getElementById('page').dataset.orderId;

async function start() {
  await loadMenu();
  const order = await getJSON(`/api/orders/${orderId}`);
  cart = order.items.map(i => ({menu_item_id: i.menu_item_id, name: i.name, qty: i.qty, addons: i.addons}));
  renderCart();
  if (!['New', 'Preparing'].includes(order.status)) {
    showError(`This order is ${order.status} and can no longer be edited.`);
    document.getElementById('save-btn').disabled = true;
  }
}

document.getElementById('save-btn').addEventListener('click', async () => {
  if (cart.length === 0) { showError('An order must keep at least one item.'); return; }
  const addressBox = document.getElementById('address');
  const result = await post(`/api/orders/${orderId}/edit`, {
    items: cartForServer(),
    address: addressBox ? addressBox.value : '',
    special_instructions: document.getElementById('special_instructions').value
  });
  if (result.ok) { window.location = '/cashier'; } else { showError(result.error); }
});

socket.on('item_availability_changed', updateMenuItem);
socket.on('order_status_changed', update => {
  if (String(update.id) === orderId) {
    document.getElementById('status-badge').textContent = update.status;
    if (update.status === 'Ready') {
      showError('The kitchen has just marked this order Ready. It can no longer be edited.');
      document.getElementById('save-btn').disabled = true;
    }
  }
});
start();
