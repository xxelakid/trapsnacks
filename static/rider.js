// static/rider.js
// RiderScreen: availability (FR 4 SR-1), offers and Accept (FR 4 SR-2/3),
// meal preparation countdown (FR 4 SR-4) and Picked up / Delivered (FR 5 SR-2).
// The countdown starts when the chef begins preparing; it stops and shows READY TO PICK UP
// as soon as the kitchen marks the order Ready.

let myStatus = 'unavailable';
let offers = {};       // delivery id -> offer
let current = null;    // my accepted delivery

const STATUS_STYLE = {available: 'bg-success', reserved: 'bg-warning text-dark', unavailable: 'bg-secondary'};

function renderStatus() {
  const badge = document.getElementById('my-status');
  badge.textContent = myStatus === 'reserved' ? 'on a delivery' : myStatus;
  badge.className = 'badge fs-6 ' + STATUS_STYLE[myStatus];
  document.getElementById('go-available').disabled = myStatus !== 'unavailable';
  document.getElementById('go-unavailable').disabled = myStatus !== 'available';
}

function renderOffers() {
  const list = Object.values(offers);
  document.getElementById('no-offers').classList.toggle('d-none', list.length > 0);
  document.getElementById('offers').innerHTML = list.map(o => `
    <div class="card card-body mb-2 offer-card">
      <div class="fs-5 fw-bold">Order #${o.order_id}</div>
      <div class="mb-2">Deliver to: ${esc(o.address)}</div>
      ${foodStatus(o.order_status, o.pickup_deadline)}
      <button class="btn btn-success btn-xl accept-btn" data-id="${o.id}">ACCEPT</button>
    </div>`).join('');
  updateCountdowns();
  document.querySelectorAll('.accept-btn').forEach(btn => btn.addEventListener('click', async () => {
    btn.disabled = true;
    const result = await post(`/api/deliveries/${btn.dataset.id}/accept`);
    if (result.ok) { setCurrent(result.data); }
    else { toast(result.error, 'warning'); delete offers[btn.dataset.id]; renderOffers(); }
  }));
}

// "Meal preparation time left" countdown, or READY TO PICK UP once the kitchen is done
function foodStatus(orderStatus, deadline) {
  if (orderStatus === 'Ready') {
    return '<div class="mb-2"><span class="badge bg-success fs-5">READY TO PICK UP</span></div>';
  }
  if (!deadline) return '';
  return `<div class="fs-5 mb-2">Meal preparation time left: <span class="countdown" data-deadline="${deadline}"></span></div>`;
}

function setCurrent(delivery) {
  current = delivery;
  if (delivery) { myStatus = 'reserved'; offers = {}; renderOffers(); }
  renderStatus(); renderCurrent();
}

function renderCurrent() {
  document.getElementById('no-current').classList.toggle('d-none', !!current);
  if (!current) { document.getElementById('current').innerHTML = ''; return; }
  const d = current;
  const ready = d.order_status === 'Ready';
  document.getElementById('current').innerHTML = `
    <div class="card border-primary">
      <div class="card-body">
        <div class="fs-4 fw-bold">Order #${d.order_id}</div>
        <div class="fs-5">${esc(d.customer_name || 'Customer')}${d.phone ? ` &middot; <a href="tel:${esc(d.phone)}">${esc(d.phone)}</a>` : ''}</div>
        <div class="fs-5 mb-2">${esc(d.address)}</div>
        ${d.special_instructions ? `<div class="instructions mb-2">${esc(d.special_instructions)}</div>` : ''}
        <ul>${d.items.map(i => `<li>${i.qty} x ${esc(i.name)}</li>`).join('')}</ul>
        ${d.status === 'Accepted' ? `
          ${foodStatus(d.order_status, d.pickup_deadline)}
          <button class="btn btn-primary btn-xl w-100 mt-3 deliv-btn" data-status="Picked up" ${ready ? '' : 'disabled'}>PICKED UP</button>`
        : `<button class="btn btn-success btn-xl w-100 mt-3 deliv-btn" data-status="Delivered">DELIVERED</button>`}
      </div>
    </div>`;
  updateCountdowns();
  document.querySelectorAll('.deliv-btn').forEach(btn => btn.addEventListener('click', async () => {
    btn.disabled = true;
    const result = await post(`/api/deliveries/${current.id}/status`, {status: btn.dataset.status});
    if (!result.ok) { toast(result.error, 'danger'); btn.disabled = false; return; }
    if (result.data.status === 'Delivered') {
      toast(`Order #${current.order_id} delivered. Thank you!`, 'success');
      current = null; myStatus = 'available'; renderStatus(); renderCurrent();
    } else { setCurrent(result.data); }
  }));
}

async function setMyStatus(status) {
  const result = await post('/api/riders/me/status', {status: status});
  if (!result.ok) { toast(result.error, 'danger'); return; }
  myStatus = status;
  if (status === 'unavailable') { offers = {}; renderOffers(); }
  renderStatus();
}
document.getElementById('go-available').addEventListener('click', () => setMyStatus('available'));
document.getElementById('go-unavailable').addEventListener('click', () => setMyStatus('unavailable'));

async function loadState() {
  const state = await getJSON('/api/rider/state');
  myStatus = state.status;
  offers = {}; state.offers.forEach(o => offers[o.id] = o);
  current = state.current;
  renderStatus(); renderOffers(); renderCurrent();
}

// Live updates
socket.on('delivery_offer', offer => {
  if (myStatus !== 'available') return;
  const isNew = !offers[offer.id];
  offers[offer.id] = offer; renderOffers();
  if (isNew) playAlert();
});
socket.on('offer_closed', closed => { delete offers[closed.id]; renderOffers(); });
socket.on('delivery_assigned', d => { setCurrent(d); playAlert(); toast(`You have order #${d.order_id}.`, 'success'); });
socket.on('delivery_updated', d => { setCurrent(d); playAlert(); toast(`Order #${d.order_id} was changed. Check the details.`, 'warning'); });
socket.on('order_ready_for_pickup', info => {
  if (current && current.order_id === info.order_id) {
    current.order_status = 'Ready'; renderCurrent(); playAlert();    // countdown stops
    toast(`Order #${info.order_id} is READY TO PICK UP.`, 'success');
  }
});
socket.on('delivery_cancelled', info => {
  toast(`Order #${info.order_id} was CANCELLED. Do not pick it up.`, 'danger'); playAlert();
  current = null; myStatus = 'available'; renderStatus(); renderCurrent();
});
socket.on('delivery_removed', info => {
  toast(`Order #${info.order_id} was given to another rider.`, 'warning');
  current = null; myStatus = 'available'; renderStatus(); renderCurrent();
});

onReconnect(loadState);
loadState();
