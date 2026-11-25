// static/order_list.js
// Order List (cashier and owner): every pickup and delivery order for a day with its status.
// Ready pickup orders get a "Collected" button. The list reloads by itself on any change.

const TODAY = document.getElementById('page').dataset.today;
const dayInput = document.getElementById('day');
const searchInput = document.getElementById('search');
const filters = {pickup: 'all', delivery: 'all'};
let allOrders = [];

const ORDER_BADGE = {New: 'bg-primary', Preparing: 'bg-warning text-dark', Ready: 'bg-success',
                     Collected: 'bg-secondary', Cancelled: 'bg-danger'};
const DELIVERY_BADGE = {Offered: 'bg-secondary', Accepted: 'bg-primary', 'Picked up': 'bg-info text-dark',
                        Delivered: 'bg-success', Cancelled: 'bg-danger'};
// Order on the screen: what needs the cashier's attention comes first
const PICKUP_ORDER = {Ready: 0, Preparing: 1, New: 2, Collected: 3, Cancelled: 4};

function money(n) { return '$' + Number(n || 0).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}); }
function itemsList(o) {
  return o.items.map(i => `${i.qty} x ${esc(i.name)}${i.addons ? ` <span class="text-muted small">(${esc(i.addons)})</span>` : ''}`).join('<br>');
}
function customer(o) { return `${esc(o.customer_name)}<div class="small text-muted">${esc(o.phone)}</div>`; }
function when(o) {
  return o.earlier
    ? `${new Date(o.created_at).toLocaleDateString()}<br><span class="badge bg-warning text-dark">From an earlier day</span>`
    : clock(o.created_at);
}

function matchesSearch(o) {
  const q = searchInput.value.trim().toLowerCase().replace(/^#/, '');
  if (!q) return true;
  return String(o.id) === q || (o.customer_name || '').toLowerCase().includes(q)
      || (o.phone || '').toLowerCase().includes(q);
}

function deliveryState(o) {
  if (o.status === 'Cancelled') return 'Cancelled';
  return o.delivery_status || 'Not sent to riders yet';
}

function renderPickup() {
  const all = allOrders.filter(o => o.order_type === 'pickup');
  const ready = all.filter(o => o.status === 'Ready').length;
  const counter = document.getElementById('ready-count');
  counter.textContent = `${ready} ready`;
  counter.classList.toggle('d-none', ready === 0);

  const f = filters.pickup;
  const list = all.filter(o => f === 'all' || o.status === f
                               || (f === 'kitchen' && ['New', 'Preparing'].includes(o.status)))
    .filter(matchesSearch)
    .sort((a, b) => (PICKUP_ORDER[a.status] - PICKUP_ORDER[b.status]) || (a.id - b.id));

  document.getElementById('no-pickup').classList.toggle('d-none', list.length > 0);
  document.getElementById('pickup-rows').innerHTML = list.map(o => `
    <tr class="${o.status === 'Ready' ? 'table-success' : ''}">
      <td class="fw-bold fs-5">#${o.id}</td>
      <td>${when(o)}</td>
      <td>${customer(o)}</td>
      <td>${itemsList(o)}</td>
      <td class="text-end">${money(o.total)}</td>
      <td><span class="badge fs-6 ${ORDER_BADGE[o.status] || 'bg-secondary'}">${o.status === 'Ready' ? 'Ready to collect' : esc(o.status)}</span>
          ${o.cancel_reason ? `<div class="small text-danger">${esc(o.cancel_reason)}</div>` : ''}</td>
      <td class="text-end">
        ${o.status === 'Ready'
          ? `<button class="btn btn-success btn-lg collect-btn" data-id="${o.id}">Collected</button>` : ''}
      </td>
    </tr>`).join('');

  // Ask first, so a mis-tap does not close the wrong order
  document.querySelectorAll('.collect-btn').forEach(btn => btn.addEventListener('click', async () => {
    if (!confirm(`Has the customer collected order #${btn.dataset.id}?`)) return;
    btn.disabled = true;
    const result = await post(`/api/orders/${btn.dataset.id}/collected`);
    if (!result.ok) { toast(result.error, 'danger'); }
    else { toast(`Order #${btn.dataset.id} marked Collected.`, 'success'); }
    loadOrders();
  }));
}

function renderDelivery() {
  const all = allOrders.filter(o => o.order_type === 'delivery');
  const onRoad = all.filter(o => o.status !== 'Cancelled' && o.delivery_status !== 'Delivered').length;
  const counter = document.getElementById('road-count');
  counter.textContent = `${onRoad} in progress`;
  counter.classList.toggle('d-none', onRoad === 0);

  const f = filters.delivery;
  const list = all.filter(o => {
      const state = deliveryState(o);
      if (f === 'all') return true;
      if (f === 'active') return !['Delivered', 'Cancelled'].includes(state);
      return state === f;
    })
    .filter(matchesSearch)
    .sort((a, b) => b.id - a.id);

  document.getElementById('no-delivery').classList.toggle('d-none', list.length > 0);
  document.getElementById('delivery-rows').innerHTML = list.map(o => {
    const state = deliveryState(o);
    return `
    <tr>
      <td class="fw-bold fs-5">#${o.id}</td>
      <td>${clock(o.created_at)}</td>
      <td>${customer(o)}</td>
      <td>${esc(o.address)}</td>
      <td>${itemsList(o)}</td>
      <td class="text-end">${money(o.total)}</td>
      <td><span class="badge ${ORDER_BADGE[o.status] || 'bg-secondary'}">${esc(o.status)}</span></td>
      <td><span class="badge fs-6 ${DELIVERY_BADGE[state] || 'bg-light text-dark border'}">${esc(state)}</span>
          ${o.cancel_reason ? `<div class="small text-danger">${esc(o.cancel_reason)}</div>` : ''}</td>
      <td>${o.rider ? esc(o.rider) : '<span class="text-muted">-</span>'}</td>
    </tr>`;
  }).join('');
}

function render() { renderPickup(); renderDelivery(); }

async function loadOrders() {
  try {
    allOrders = await getJSON(`/api/orders/list?date=${encodeURIComponent(dayInput.value || TODAY)}`);
    render();
  } catch (err) {
    toast('Could not load the orders. Check the connection.', 'danger');
  }
}

// Filters, search and day
document.querySelectorAll('.filter-group').forEach(group => {
  group.querySelectorAll('button').forEach(btn => btn.addEventListener('click', () => {
    group.querySelectorAll('button').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    filters[group.dataset.list] = btn.dataset.filter;
    render();
  }));
});
searchInput.addEventListener('input', render);
dayInput.addEventListener('change', loadOrders);
document.getElementById('today-btn').addEventListener('click', () => { dayInput.value = TODAY; loadOrders(); });

// Live updates: any change reloads the list (grouped so a burst of changes loads once)
let reloadTimer = null;
function reloadSoon() { clearTimeout(reloadTimer); reloadTimer = setTimeout(loadOrders, 300); }
['order_created', 'order_edited', 'order_status_changed', 'order_cancelled', 'delivery_changed']
  .forEach(event => socket.on(event, reloadSoon));
socket.on('staff_alert', a => toast(a.message, 'info'));

onReconnect(loadOrders);
loadOrders();
