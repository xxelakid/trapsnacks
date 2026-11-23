// static/order_form.js
// The menu buttons and the "cart" (items in the order). Used by the cashier and edit pages.

let menuItems = [];   // everything on the menu
let cart = [];        // [{menu_item_id, name, qty, addons}]

async function loadMenu() {
  menuItems = await getJSON('/api/menu');
  renderMenu();
}

function renderMenu() {
  const byCategory = {};
  menuItems.forEach(item => (byCategory[item.category] = byCategory[item.category] || []).push(item));
  document.getElementById('menu').innerHTML = Object.keys(byCategory).map(category => `
    <h3 class="h6 text-muted mt-2">${esc(category)}</h3>
    <div class="d-flex flex-wrap gap-2">
      ${byCategory[category].map(item => `
        <button class="btn ${item.available ? 'btn-outline-dark' : 'btn-outline-secondary'} menu-btn"
                data-id="${item.id}" ${item.available ? '' : 'disabled'}>
          ${esc(item.name)}<br><small>${item.available ? '$' + item.price : 'UNAVAILABLE'}</small>
        </button>`).join('')}
    </div>`).join('');
  document.querySelectorAll('.menu-btn').forEach(btn =>
    btn.addEventListener('click', () => addToCart(Number(btn.dataset.id))));
}

// FR 6 SR-2/SR-3: called when the kitchen changes an item's availability
function updateMenuItem(changed) {
  const item = menuItems.find(i => i.id === changed.id);
  if (item) item.available = changed.available;
  renderMenu();
  if (!changed.available && cart.some(c => c.menu_item_id === changed.id)) {
    toast(`${changed.name} is now unavailable. Remove it from the order.`, 'warning');
  }
}

function addToCart(menuItemId) {
  const item = menuItems.find(i => i.id === menuItemId);
  const line = cart.find(c => c.menu_item_id === menuItemId && !c.addons);
  if (line) { line.qty += 1; } else { cart.push({menu_item_id: item.id, name: item.name, qty: 1, addons: ''}); }
  showError('');
  renderCart();
}

function renderCart() {
  const box = document.getElementById('cart');
  if (cart.length === 0) { box.innerHTML = '<p class="text-muted mb-0">Tap menu items to add them.</p>'; return; }
  box.innerHTML = cart.map((line, i) => `
    <div class="d-flex align-items-center gap-2 mb-2 cart-line">
      <button class="btn btn-outline-secondary qty-btn" data-i="${i}" data-change="-1">-</button>
      <span class="fs-5 qty">${line.qty}</span>
      <button class="btn btn-outline-secondary qty-btn" data-i="${i}" data-change="1">+</button>
      <span class="flex-grow-1">${esc(line.name)}</span>
      <input class="form-control form-control-sm addons" style="max-width: 14rem" data-i="${i}"
             placeholder="Add-ons (e.g. extra cheese)" value="${esc(line.addons)}">
      <button class="btn btn-outline-danger remove-btn" data-i="${i}">x</button>
    </div>`).join('');
  box.querySelectorAll('.qty-btn').forEach(b => b.addEventListener('click', () => {
    const line = cart[b.dataset.i];
    line.qty += Number(b.dataset.change);
    if (line.qty < 1) cart.splice(b.dataset.i, 1);
    renderCart();
  }));
  box.querySelectorAll('.remove-btn').forEach(b => b.addEventListener('click', () => { cart.splice(b.dataset.i, 1); renderCart(); }));
  box.querySelectorAll('.addons').forEach(input => input.addEventListener('input', () => { cart[input.dataset.i].addons = input.value; }));
}

// The items in the format the server expects
function cartForServer() {
  return cart.map(line => ({id: line.menu_item_id, qty: line.qty, addons: line.addons}));
}

function showError(message) {
  const box = document.getElementById('order-error');
  if (message) { box.textContent = message; box.classList.remove('d-none'); }
  else { box.classList.add('d-none'); }
}
