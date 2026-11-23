// static/app.js
// Helpers shared by every page: sending data, live updates, sound, countdowns and messages.

const csrfToken = document.querySelector('meta[name=csrf-token]').content;

// Sends data to the server and returns {ok, data} or {ok: false, error}.
async function post(url, data) {
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrfToken},
      body: JSON.stringify(data || {})
    });
    const body = await response.json();
    return body.ok ? {ok: true, data: body.data} : {ok: false, error: body.error || 'Something went wrong.'};
  } catch (err) {
    return {ok: false, error: 'Could not reach the server. Check the Wi-Fi connection.'};
  }
}

// Gets data from the server.
async function getJSON(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error('Request failed: ' + url);
  return response.json();
}

// Makes text safe to put inside HTML (stops a customer's note from breaking the page).
function esc(text) {
  return String(text ?? '').replace(/[&<>"']/g, ch =>
    ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[ch]));
}

// Short pop-up message in the corner.
function toast(message, kind) {
  const box = document.createElement('div');
  box.className = `alert alert-${kind || 'info'} shadow`;
  box.textContent = message;
  document.getElementById('toast-area').appendChild(box);
  setTimeout(() => box.remove(), 6000);
}

// "08:15 AM" style time
function clock(iso) {
  return iso ? new Date(iso).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'}) : '';
}

// Whole minutes since a time
function minutesSince(iso) {
  return Math.floor((Date.now() - new Date(iso)) / 60000);
}

// ---------- Sound (browsers only allow sound after the user taps the page once) ----------
const alertSound = new Audio('/static/alert.wav');
let soundOn = false;
function playAlert() {
  if (!soundOn) return;
  alertSound.currentTime = 0;
  alertSound.play().catch(() => {});
}
const soundButton = document.getElementById('sound-btn');
if (soundButton) {
  soundButton.addEventListener('click', () => {
    soundOn = true;
    alertSound.play().catch(() => {});
    soundButton.textContent = 'Sound on';
    soundButton.classList.replace('btn-outline-warning', 'btn-warning');
  });
}

// ---------- Hooks that page scripts can add to ----------
// onTick(fn): run fn every second.  onReconnect(fn): run fn after the connection comes back.
// Several scripts on one page (for example kitchen.js and kitchen_availability.js) can each add one.
const tickHandlers = [];
const reconnectHandlers = [];
function onTick(handler) { tickHandlers.push(handler); }
function onReconnect(handler) { reconnectHandlers.push(handler); }

// ---------- Countdowns: any element with data-deadline="2026-11-20T10:30:00" ----------
function updateCountdowns() {
  document.querySelectorAll('[data-deadline]').forEach(el => {
    const secondsLeft = Math.round((new Date(el.dataset.deadline) - Date.now()) / 1000);
    if (secondsLeft <= 0) {
      el.textContent = 'LATE';
      el.classList.add('late');
    } else {
      const m = Math.floor(secondsLeft / 60), s = secondsLeft % 60;
      el.textContent = `${m}:${String(s).padStart(2, '0')}`;
      el.classList.remove('late');
    }
  });
  tickHandlers.forEach(handler => handler());   // pages add their own checks with onTick(...)
}
setInterval(updateCountdowns, 1000);

// ---------- Live updates (Socket.IO) ----------
let socket = null;
if (document.body.dataset.live === '1') {
  socket = io();
  const banner = document.getElementById('offline-banner');
  let firstConnect = true;
  socket.on('disconnect', () => banner.classList.remove('d-none'));
  socket.on('connect', () => {
    banner.classList.add('d-none');
    // After a reconnect, reload the page's data so nothing is missed (QA: reliability).
    if (!firstConnect) reconnectHandlers.forEach(handler => handler());
    firstConnect = false;
  });
}
