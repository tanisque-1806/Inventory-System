/* ============================================================
   api.js — Shared API helper for all frontend pages
   ============================================================ */

const BASE = '/api';

function getToken() {
  return localStorage.getItem('token');
}
function getUser()  { return JSON.parse(localStorage.getItem('user') || 'null'); }
function getRole()  { return localStorage.getItem('role'); }

async function logout() {
  try { await fetch(BASE + '/auth/logout', { method: 'POST', credentials: 'include' }); } catch (_) {}
  localStorage.clear();
  window.location.href = '/login.html';
}

async function apiFetch(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  const res = await fetch(BASE + path, { ...options, headers, credentials: 'include' });
  const data = await res.json().catch(() => ({}));

  if (res.status === 401) { logout(); return null; }
  return data;
}

const api = {
  get:    (path)         => apiFetch(path, { method: 'GET' }),
  post:   (path, body)   => apiFetch(path, { method: 'POST',   body: JSON.stringify(body) }),
  put:    (path, body)   => apiFetch(path, { method: 'PUT',    body: JSON.stringify(body) }),
  delete: (path)         => apiFetch(path, { method: 'DELETE' }),
  patch:  (path, body)   => apiFetch(path, { method: 'PATCH',  body: JSON.stringify(body) }),
};

/* ── Toast ──────────────────────────────────────────────────── */
function toast(msg, type = 'default') {
  let c = document.getElementById('toast-container');
  if (!c) { c = document.createElement('div'); c.id = 'toast-container'; document.body.appendChild(c); }
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  const icons = { success: '✅', error: '❌', warning: '⚠️', default: 'ℹ️' };
  t.innerHTML = `<span>${icons[type] || icons.default}</span><span>${msg}</span>`;
  c.appendChild(t);
  setTimeout(() => t.remove(), 3500);
}

/* ── Modal helpers ──────────────────────────────────────────── */
function openModal(id)  { document.getElementById(id)?.classList.add('open'); }
function closeModal(id) { document.getElementById(id)?.classList.remove('open'); }

/* ── Format helpers ─────────────────────────────────────────── */
function fmt(n)   { return '₹' + Number(n || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 }); }
function date(d)  { return d ? new Date(d).toLocaleDateString('en-IN', { day:'2-digit', month:'short', year:'numeric' }) : '—'; }
function time(d)  { return d ? new Date(d).toLocaleTimeString('en-IN', { hour:'2-digit', minute:'2-digit' }) : '—'; }

function statusBadge(s) {
  const map = {
    PENDING:'badge-yellow', CONFIRMED:'badge-blue', SHIPPED:'badge-purple',
    DELIVERED:'badge-green', CANCELLED:'badge-red',
    APPROVED:'badge-green', REJECTED:'badge-red',
    LOW_STOCK:'badge-red', ORDER:'badge-blue', SUPPLY:'badge-purple', SYSTEM:'badge-gray'
  };
  return `<span class="badge ${map[s] || 'badge-gray'}">${s}</span>`;
}

/* ── Guard ──────────────────────────────────────────────────── */
function requireRole(...roles) {
  const role = getRole();
  if (!role || !roles.includes(role)) { logout(); }
}

/* ── Set active nav ─────────────────────────────────────────── */
function setActiveNav(path) {
  document.querySelectorAll('.nav-item').forEach(el => {
    if (el.dataset.href === path) el.classList.add('active');
    else el.classList.remove('active');
  });
}

/* ── Populate user info in sidebar ─────────────────────────── */
function initSidebar() {
  const user = getUser();
  if (!user) return;
  const el = document.getElementById('sidebar-user-name');
  const av = document.getElementById('sidebar-avatar');
  const rl = document.getElementById('sidebar-role');
  if (el) el.textContent = user.name;
  if (av) av.textContent = (user.name || 'U')[0].toUpperCase();
  if (rl) rl.textContent = getRole();
}

/* ── Notification badge ─────────────────────────────────────── */
async function loadNotifBadge() {
  const data = await api.get('/admin/notifications');
  const count = data?.data?.unreadCount || 0;
  const badge = document.getElementById('notif-badge');
  const dot   = document.getElementById('notif-dot');
  if (badge) badge.textContent = count > 0 ? count : '';
  if (dot)   dot.style.display = count > 0 ? 'block' : 'none';
}
