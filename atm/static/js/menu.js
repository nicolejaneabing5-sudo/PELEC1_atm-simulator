(() => {
  'use strict';

  const $ = (sel, root = document) => root.querySelector(sel);
  const btn = $('#menuBtn');
  const menu = $('#menuDropdown');
  if (!btn || !menu) return;

  const esc = s => String(s).replace(/[&<>"']/g, c =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const row = (k, v) => `<div class="info-row"><span>${esc(k)}</span><strong>${esc(v)}</strong></div>`;
  const section = t => `<div class="info-section">${esc(t)}</div>`;

   // ---------- dropdown ----------
  function setMenu(open) {
    menu.hidden = !open;
    btn.setAttribute('aria-expanded', String(open));
  }
  btn.addEventListener('click', e => { e.stopPropagation(); setMenu(menu.hidden); });
  document.addEventListener('click', e => { if (!menu.contains(e.target)) setMenu(false); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape') setMenu(false); });

  const closeBtn = $('#menuClose');
  if (closeBtn) closeBtn.addEventListener('click', () => setMenu(false));

      // ---------- logout: reuse the header's card-eject animation ----------
  const logout = $('#menuLogout');
  const lockLink = document.querySelector('.user-menu[data-lock-session]');
  if (logout && lockLink) {
    logout.addEventListener('click', e => {
      e.preventDefault();
      setMenu(false);      // close the dropdown so it doesn't cover the animation
      lockLink.click();    // same click as the header button, so the card ejects
    });
  }

  // ---------- dialogs ----------
  async function load(dialog, target, render) {
    target.textContent = 'Loading…';
    try {
      const res = await fetch(dialog.dataset.url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
      if (res.status === 401) { window.location.href = '/'; return; }
      target.innerHTML = render(await res.json());
    } catch (err) {
      target.textContent = 'Could not load this right now. Please try again.';
    }
  }

  const renderers = {
    accountDialog: d => {
      const h = d.holder, c = d.card, s = d.security;
      let html = section('Account holder') + row('Name', h.name) + row('Customer ID', h.customer_id) +
        row('Email', h.email) + row('Mobile', h.mobile) + row('Customer since', h.customer_since) +
        row('Customer tier', h.tier);
      d.accounts.forEach(a => {
        html += section(a.type) + row('Account number', a.number) + row('Status', a.status) +
          row('Date opened', a.opened) + row('Branch', a.branch) + row('Currency', a.currency) +
          row('Current balance', a.balance) + row('Minimum balance', a.min_balance) +
          row('Interest rate', a.interest);
      });
      html += section('Debit card') + row('Card number', c.number) + row('Expiry', c.expiry) + row('Status', c.status);
      html += section('Security') + row('Last login', s.last_login) + row('PIN last changed', s.pin_changed);
      return html;
    },
    limitDialog: d => d.accounts.map(a => `
      <div class="limit-card">
        <h3>${esc(a.name)} (•••• ${esc(a.last4)})</h3>
        ${row('Per transaction', a.max_tx)}
        ${row('Daily limit', a.daily_max)}
        ${row('Withdrawn today', a.used)}
        ${row('Daily limit remaining', a.remaining)}
        ${row('Available to withdraw now', a.available)}
        <div class="limit-bar"><div class="${a.pct >= 80 ? 'high' : ''}" style="width:${a.pct}%"></div></div>
        <small>A minimum balance of ${esc(a.min_balance)} must remain after every withdrawal.</small>
      </div>`).join('')
  };

  const bodies = { accountDialog: '#accountBody', limitDialog: '#limitBody' };

  document.querySelectorAll('[data-dialog]').forEach(item => item.addEventListener('click', () => {
    setMenu(false);
    const dialog = document.getElementById(item.dataset.dialog);
    if (!dialog) return;
    if (!dialog.open) dialog.showModal();
    if (renderers[dialog.id]) load(dialog, $(bodies[dialog.id]), renderers[dialog.id]);
    if (dialog.id === 'pinDialog') resetPinForm();
  }));

  document.querySelectorAll('.menu-dialog').forEach(dialog => {
    dialog.addEventListener('click', e => {
      if (e.target === dialog || e.target.closest('[data-close]')) dialog.close();
    });
  });

  // ---------- change PIN ----------
  const form = $('#pinForm');
  const msg = $('#pinMsg');

    // numbers only: strip anything that isn't 0-9 while typing, pasting or dropping
  const digitInputs = form.querySelectorAll('[data-digits]');
  digitInputs.forEach(input => {
    input.addEventListener('beforeinput', e => {
      // block letters/symbols before they even appear
      if (e.data && /\D/.test(e.data)) e.preventDefault();
    });
    input.addEventListener('input', () => {
      input.value = input.value.replace(/\D/g, '').slice(0, 4);
    });
    input.addEventListener('paste', e => {
      e.preventDefault();
      const text = (e.clipboardData || window.clipboardData).getData('text');
      input.value = text.replace(/\D/g, '').slice(0, 4);
    });
  });

  function showMsg(text, ok) {
    msg.hidden = false;
    msg.textContent = text;
    msg.className = 'pin-msg ' + (ok ? 'ok' : 'err');
  }
  function resetPinForm() { form.reset(); msg.hidden = true; }

  form.addEventListener('submit', async e => {
    e.preventDefault();

        const allDigits = [...digitInputs].every(i => /^\d{4}$/.test(i.value));
    if (!allDigits) {
      showMsg('PINs must be exactly 4 digits (numbers only).', false);
      return;
    }
 
    const submit = $('button[type="submit"]', form);
    submit.disabled = true;
    try {
      const res = await fetch(form.action, {
        method: 'POST',
        body: new FormData(form),
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      });
      const data = await res.json();
      if (data.locked) { window.location.href = data.redirect || '/'; return; }
      if (res.status === 401) { window.location.href = '/'; return; }
      showMsg(data.message, data.ok);
      if (data.ok) form.reset();
    } catch (err) {
      showMsg('Could not reach the server. Please try again.', false);
    } finally {
      submit.disabled = false;
    }
  });
})();