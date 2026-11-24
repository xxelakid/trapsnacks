// static/deliveries.js
// DeliveryDisplayScreen: active deliveries, countdowns, alerts and manual assignment
// (FR 4 SR-4/SR-5, FR 5).

const page = document.getElementById('page');
const ALERT_MINUTES = Number(page.dataset.alertMinutes);
const IS_OWNER = page.dataset.isOwner === '1';
const deliveries = {};       // id -> delivery
let availableRiders = [];

if (!IS_OWNER) document.querySelectorAll('.owner-only').forEach(el => el.classList.add('d-none'));

const STATUS_STYLE = {Offered: 'bg-secondary', Accepted: 'bg-primary', 'Picked up': 'bg-info text-dark'};

function noRiderTooLong(d) {
  return d.status === 'Offered' && (Date.now() - new Date(d.offered_at)) / 60000 >= ALERT_MINUTES;
}

function renderActive() {
  const list = Object.values(deliveries).sort((a, b) => new Date(a.offered_at) - new Date(b.offered_at));
  document.getElementById('no-active').classList.toggle('d-none', list.length > 0);
  document.getElementById('active').innerHTML = list.map(d => `
    <tr data-id="${d.id}">
      <td class="fw-bold fs-5">#${d.order_id}</td>
      <td>${esc(d.rider)}</td>
      <td><span class="badge fs-6 ${STATUS_STYLE[d.status] || 'bg-secondary'}">${d.status}</span></td>
      <td>${esc(d.order_status)}</td>
      <td class="fs-5">${d.status === 'Accepted' ? `<span data-deadline="${d.pickup_deadline}"></span>`
                       : d.status === 'Picked up' ? 'Picked up at ' + clock(d.picked_up_at) : '-'}</td>
      <td class="alert-cell"></td>
      <td class="owner-only ${IS_OWNER ? '' : 'd-none'}">
        ${d.status !== 'Picked up' ? `
          <div class="input-group input-group-sm" style="max-width: 18rem">
            <select class="form-select assign-select">
              <option value="">Choose rider...</option>
              ${availableRiders.map(r => `<option value="${r.id}">${esc(r.name)}</option>`).join('')}
            </select>
            <button class="btn btn-outline-primary assign-btn" data-id="${d.id}">Assign</button>
          </div>` : ''}
      </td>
    </tr>`).join('');
  updateCountdowns();
  updateAlerts();
  document.querySelectorAll('.assign-btn').forEach(btn => btn.addEventListener('click', async () => {
    const riderId = btn.parentElement.querySelector('.assign-select').value;
    if (!riderId) { toast('Choose a rider first.', 'warning'); return; }
    const result = await post(`/api/deliveries/${btn.dataset.id}/assign`, {rider_id: riderId});
    if (!result.ok) toast(result.error, 'danger');
  }));
}

// FR 4 SR-5: "no rider yet" and "late" alerts, checked every second
function updateAlerts() {
  document.querySelectorAll('#active tr').forEach(row => {
    const d = deliveries[row.dataset.id];
    const cell = row.querySelector('.alert-cell');
    let html = '';
    if (noRiderTooLong(d)) html = '<span class="badge bg-danger fs-6">No rider has accepted!</span>';
    if (d.status === 'Accepted' && new Date(d.pickup_deadline) < Date.now()) html = '<span class="badge bg-danger fs-6">LATE</span>';
    if (cell.innerHTML !== html) cell.innerHTML = html;
    row.classList.toggle('table-danger', html !== '');
  });
}
onTick(updateAlerts);

async function loadRiders() {
  if (!IS_OWNER) return;
  availableRiders = await getJSON('/api/riders/available');
}

async function loadActive() {
  await loadRiders();
  const list = await getJSON('/api/deliveries/active');
  Object.keys(deliveries).forEach(id => delete deliveries[id]);
  list.forEach(d => deliveries[d.id] = d);
  renderActive();
}

async function loadHistory() {
  const list = await getJSON('/api/deliveries/history');
  document.getElementById('history').innerHTML = list.map(d => {
    const minutes = d.picked_up_at && d.delivered_at
      ? Math.round((new Date(d.delivered_at) - new Date(d.picked_up_at)) / 60000) : '';
    const onTime = d.pickup_deadline && d.picked_up_at && new Date(d.picked_up_at) <= new Date(d.pickup_deadline);
    return `<tr><td>#${d.order_id}</td><td>${new Date(d.delivered_at).toLocaleDateString()}</td>
      <td>${esc(d.rider)}</td><td>${clock(d.picked_up_at)}</td><td>${clock(d.delivered_at)}</td>
      <td>${minutes}</td><td>${onTime ? 'Yes' : '<span class="text-danger">Late pickup</span>'}</td></tr>`;
  }).join('') || '<tr><td colspan="7" class="text-muted">No completed deliveries yet.</td></tr>';
}
document.getElementById('history-tab').addEventListener('click', loadHistory);

// Live updates
socket.on('delivery_changed', d => {
  if (['Offered', 'Accepted', 'Picked up'].includes(d.status)) { deliveries[d.id] = d; }
  else { delete deliveries[d.id]; }     // Delivered or Cancelled leave the active list
  renderActive();
});
socket.on('order_status_changed', update => {
  Object.values(deliveries).forEach(d => { if (d.order_id === update.id) d.order_status = update.status; });
  renderActive();
});
socket.on('rider_changed', async () => { await loadRiders(); renderActive(); });
socket.on('staff_alert', a => toast(a.message, 'info'));

onReconnect(loadActive);
loadActive();
