// static/cashier.js
// OrderScreen: create orders (FR 0) and watch their status (FR 1 SR-2).

const orders = {};   // order id -> order
const page = document.getElementById('page');
const CAN_EDIT = page.dataset.canEdit === '1';       // FR 2 added?
const CAN_CANCEL = page.dataset.canCancel === '1';   // FR 3 added?

function setOrderType(type) {
  document.getElementById('address-box').classList.toggle('d-none', type !== 'delivery');
}
document.querySelectorAll('input[name=order_type]').forEach(r =>
  r.addEventListener('change', () => setOrderType(r.value)));

document.getElementById('confirm-btn').addEventListener('click', async () => {
  const type = document.querySelector('input[name=order_type]:checked');
  // Tell the cashier what is missing before sending (FR 0 SR-1). The server checks again.
  const missing = [];
  if (cart.length === 0) missing.push('at least one item');
  if (!type) missing.push('Pickup or Delivery');
  if (type && type.value === 'delivery' && !document.getElementById('address').value.trim()) missing.push('the delivery address');
  if (missing.length) { showError('Please add: ' + missing.join(', ') + '.'); return; }

  const button = document.getElementById('confirm-btn');
  button.disabled = true;                               // stops double-tapping
  const result = await post('/api/orders', {
    order_type: type.value,
    customer_name: document.getElementById('customer_name').value,
    phone: document.getElementById('phone').value,
    address: document.getElementById('address').value,
    special_instructions: document.getElementById('special_instructions').value,
    items: cartForServer()
  });
  button.disabled = false;
  if (!result.ok) { showError(result.error); return; }

  showError('');
  toast(`Order #${result.data.id} sent to the kitchen.`, 'success');
  cart = []; renderCart();
  ['customer_name', 'phone', 'address', 'special_instructions'].forEach(id => document.getElementById(id).value = '');
  document.querySelectorAll('input[name=order_type]').forEach(r => r.checked = false);
  setOrderType(null);
  upsertOrder(result.data);
});

const STATUS_COLOURS = {New: 'bg-primary', Preparing: 'bg-warning text-dark', Ready: 'bg-success'};

function upsertOrder(order) {
  if (order.status === 'Cancelled') { delete orders[order.id]; } else { orders[order.id] = order; }
  renderOrders();
}

function renderOrders() {
  const list = Object.values(orders).sort((a, b) => b.id - a.id);
  document.getElementById('no-orders').classList.toggle('d-none', list.length > 0);
  document.getElementById('orders').innerHTML = list.map(o => `
    <tr>
      <td class="fw-bold">${o.id}</td>
      <td>${clock(o.created_at)}</td>
      <td>${o.order_type === 'delivery' ? 'Delivery' : 'Pickup'}${o.delivery_status ? `<br><small class="text-muted">${esc(o.delivery_status)}</small>` : ''}</td>
      <td>${o.items.map(i => `${i.qty} x ${esc(i.name)}`).join('<br>')}</td>
      <td><span class="badge fs-6 ${STATUS_COLOURS[o.status] || 'bg-secondary'}">${o.status}</span>
          ${o.edited ? '<span class="badge bg-info text-dark">Edited</span>' : ''}</td>
      <td class="text-end text-nowrap">
        ${['New', 'Preparing'].includes(o.status) ? `
          ${CAN_EDIT ? `<a class="btn btn-sm btn-outline-primary" href="/orders/${o.id}/edit">Edit</a>` : ''}
          ${CAN_CANCEL ? `<a class="btn btn-sm btn-outline-danger" href="/orders/${o.id}/cancel">Cancel</a>` : ''}` : ''}
      </td>
    </tr>`).join('');
}

async function loadOrders() {
  const list = await getJSON('/api/orders/active');
  Object.keys(orders).forEach(id => delete orders[id]);
  list.forEach(o => orders[o.id] = o);
  renderOrders();
}

// Live updates
socket.on('order_created', upsertOrder);
socket.on('order_edited', upsertOrder);
socket.on('order_status_changed', update => {
  if (orders[update.id]) { orders[update.id].status = update.status; renderOrders(); }
});
socket.on('order_cancelled', update => { delete orders[update.id]; renderOrders(); });
socket.on('item_availability_changed', updateMenuItem);
socket.on('delivery_changed', d => {
  if (orders[d.order_id]) { orders[d.order_id].delivery_status = d.status; renderOrders(); }
});
socket.on('staff_alert', a => toast(a.message, 'info'));

onReconnect(() => { loadMenu(); loadOrders(); });
loadMenu(); renderCart(); loadOrders();
