// static/kitchen.js
// KitchenDisplayScreen: orders oldest first (FR 1), edits (FR 2) and cancellations (FR 3).
// Delivery orders being prepared show the meal preparation countdown (PREP_MINUTES).
// The item availability panel (FR 6) is in kitchen_availability.js.

const orders = {};           // id -> order
const changes = {};          // id -> {added: [...], removed: [...]} after an edit (FR 2 SR-2)

function itemKey(i) { return `${i.qty} x ${i.name}${i.addons ? ' (' + i.addons + ')' : ''}`; }

function renderOrders() {
  const list = Object.values(orders).sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
  document.getElementById('no-orders').classList.toggle('d-none', list.length > 0);
  document.getElementById('orders').innerHTML = list.map(o => {
    const diff = changes[o.id];
    const added = diff ? diff.added : [];
    return `
    <div class="card kitchen-card ${o.status === 'Preparing' ? 'border-warning' : 'border-primary'}">
      <div class="card-header d-flex justify-content-between">
        <span class="fs-4 fw-bold">#${o.id}</span>
        <span class="fs-5">${o.order_type === 'delivery' ? 'DELIVERY' : 'PICKUP'}</span>
        <span class="fs-5" data-since="${o.created_at}">${minutesSince(o.created_at)} min</span>
      </div>
      <div class="card-body">
        ${diff ? `<div class="alert alert-info py-1 mb-2 fw-bold">EDITED
            <button class="btn btn-sm btn-dark float-end ack-btn" data-id="${o.id}">Acknowledge</button></div>` : ''}
        <ul class="list-unstyled fs-5 mb-2">
          ${o.items.map(i => `<li class="${added.includes(itemKey(i)) ? 'changed' : ''}">${esc(itemKey(i))}</li>`).join('')}
          ${diff ? diff.removed.map(r => `<li class="removed">${esc(r)}</li>`).join('') : ''}
        </ul>
        ${o.special_instructions ? `<div class="instructions">${esc(o.special_instructions)}</div>` : ''}
        ${o.status === 'Preparing' && o.prep_deadline ? `
          <div class="prep-timer mt-2">Prep time left <span class="countdown" data-deadline="${o.prep_deadline}"></span></div>` : ''}
      </div>
      <div class="card-footer">
        ${o.status === 'New'
          ? `<button class="btn btn-warning btn-xl w-100 status-btn" data-id="${o.id}" data-status="Preparing">Start preparing</button>`
          : `<button class="btn btn-success btn-xl w-100 status-btn" data-id="${o.id}" data-status="Ready">Mark READY</button>`}
      </div>
    </div>`;
  }).join('');
  updateCountdowns();          // fill in the countdowns straight away

  document.querySelectorAll('.status-btn').forEach(btn => btn.addEventListener('click', async () => {
    btn.disabled = true;
    const result = await post(`/api/orders/${btn.dataset.id}/status`, {status: btn.dataset.status});
    if (!result.ok) { toast(result.error, 'danger'); btn.disabled = false; }
  }));
  document.querySelectorAll('.ack-btn').forEach(btn => btn.addEventListener('click', () => {
    delete changes[btn.dataset.id]; renderOrders();
  }));
}

// Update the "minutes waiting" every few seconds
onTick(() => document.querySelectorAll('[data-since]').forEach(el =>
  el.textContent = `${minutesSince(el.dataset.since)} min`));

async function loadOrders() {
  const list = await getJSON('/api/orders/active');
  Object.keys(orders).forEach(id => delete orders[id]);
  list.filter(o => o.status === 'New' || o.status === 'Preparing').forEach(o => orders[o.id] = o);
  renderOrders();
}

// ---- Live updates ----
socket.on('order_created', order => { orders[order.id] = order; renderOrders(); playAlert(); });
socket.on('order_status_changed', update => {
  if (!orders[update.id]) return;
  if (update.status === 'New' || update.status === 'Preparing') {
    orders[update.id].status = update.status;
    if (update.prep_deadline) orders[update.id].prep_deadline = update.prep_deadline;   // countdown starts
  }
  else { delete orders[update.id]; delete changes[update.id]; }   // Ready orders leave the kitchen screen
  renderOrders();
});
socket.on('order_edited', order => {
  const before = orders[order.id] ? orders[order.id].items.map(itemKey) : [];
  const after = order.items.map(itemKey);
  changes[order.id] = {added: after.filter(k => !before.includes(k)), removed: before.filter(k => !after.includes(k))};
  orders[order.id] = order;
  renderOrders(); playAlert();
});
socket.on('order_cancelled', update => {
  delete orders[update.id]; delete changes[update.id]; renderOrders(); playAlert();
  const alertBox = document.createElement('div');
  alertBox.className = 'alert alert-danger fs-4 fw-bold d-flex justify-content-between';
  alertBox.innerHTML = `<span>Order #${update.id} was CANCELLED (${esc(update.reason)}). Stop preparing it.</span>
                        <button class="btn btn-light">OK</button>`;
  alertBox.querySelector('button').addEventListener('click', () => alertBox.remove());
  document.getElementById('cancel-alerts').prepend(alertBox);
});

onReconnect(loadOrders);
loadOrders();
