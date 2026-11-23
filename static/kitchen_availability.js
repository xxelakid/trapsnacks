// static/kitchen_availability.js
// FR 6 Item Availability: the panel on the kitchen screen where the chef marks
// menu items available or unavailable. kitchen.html only loads this file once FR 6 exists.

let menu = [];

async function loadMenu() {
  menu = await getJSON('/api/menu');
  renderMenu();
}

function renderMenu() {
  document.getElementById('availability').innerHTML = menu.map(item => `
    <button class="btn ${item.available ? 'btn-outline-success' : 'btn-danger'} avail-btn"
            data-id="${item.id}" data-available="${item.available ? '0' : '1'}">
      ${esc(item.name)}: ${item.available ? 'Available' : 'UNAVAILABLE'}
    </button>`).join('');
  document.querySelectorAll('.avail-btn').forEach(btn => btn.addEventListener('click', async () => {
    const result = await post(`/api/menu/${btn.dataset.id}/availability`, {available: btn.dataset.available === '1'});
    if (!result.ok) toast(result.error, 'danger');
  }));
}

// Keep the panel in step when another kitchen screen changes an item
socket.on('item_availability_changed', item => {
  const found = menu.find(m => m.id === item.id);
  if (found) found.available = item.available;
  renderMenu();
});

onReconnect(loadMenu);
loadMenu();
