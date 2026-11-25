'use strict';

/* elements */
const $ = id => document.getElementById(id);
const txForm      = $('tx-form');
const amountInput = $('amount');
const amountField = document.querySelector('.amount-field');
const message     = $('tx-message');
const submitBtn   = txForm.querySelector('[type="submit"]');
const submitLabel = $('tx-submit-label');
const txList      = $('tx-list');
const historyList = $('history-list');

const selectedRadio = name => document.querySelector(`input[name="${name}"]:checked`);
const selectedKey   = () => selectedRadio('account').value;
const selectedType  = () => selectedRadio('tx-type').value;
const selectedCard  = () => selectedRadio('account').closest('.account-card');

/* csrf */
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return '';
}

function getCsrfToken() {
    // 1) hidden input from {% csrf_token %} (inside or anywhere on the page)
    const input = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (input && input.value) return input.value;
    // 2) fall back to the cookie Django sets
    return getCookie('csrftoken');
}

/* greetings */
const greeting = $('greeting-title');
const hour = new Date().getHours();
if (greeting) {
    greeting.textContent =
        `Good ${hour < 12 ? 'morning' : hour < 18 ? 'afternoon' : 'evening'}, ${greeting.dataset.name}`;
}

/* notifications */
const bellBtn       = $('notificationBell');
const notifDropdown = $('notificationDropdown');
const notifList     = $('notificationList');
const notifBadge    = $('notifBadge');
const notifHeader   = $('notifHeaderTitle');
const markAllBtn    = $('markAllReadBtn');
const notifViewAll  = $('notifViewAll');
const notifBackdrop = $('notifBackdrop');
const notifClose    = $('notifClose');
const allNotifList  = $('allNotificationsList');

/* open / close the right-side drawer */
function setNotifOpen(open) {
    notifDropdown?.classList.toggle('show', open);
    notifBackdrop?.classList.toggle('show', open);
    notifDropdown?.setAttribute('aria-hidden', String(!open));
    bellBtn?.setAttribute('aria-expanded', String(open));
}

function updateNotifCount() {
    if (!notifList || !notifBadge || !notifHeader) return;
    const unreadCount = notifList.querySelectorAll('.notification-item.unread').length;
    notifHeader.textContent = `Notifications (${unreadCount})`;
    notifBadge.textContent  = unreadCount;
    notifBadge.style.display = unreadCount > 0 ? 'flex' : 'none';
}

function markItemRead(item) {
    if (!item || !item.classList.contains('unread')) return;
    item.classList.remove('unread');
    const dot = item.querySelector('.unread-dot');
    if (dot) dot.remove();
    updateNotifCount();
}

function addNotification(row) {
    if (!notifList || !row) return;
    const d = row.dataset;
    const isIn = d.kind === 'in';
    const time  = new Date().toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
    const stamp = /\d{1,2}:\d{2}/.test(d.date) ? d.date : `${d.date} • ${time}`;
    const title = isIn
        ? `Account Notice: ${d.signed.replace('+', '')} deposit received for ${d.account}.`
        : `Transaction Alert: Withdrawal of ${d.signed.replace('-', '')} from ${d.account} was successful.`;

    const item = document.createElement('div');
    item.className = 'notification-item unread';
    item.dataset.action  = 'receipt';
    item.dataset.kind    = d.kind;
    item.dataset.signed  = d.signed;
    item.dataset.type    = d.type;
    item.dataset.account = d.account;
    item.dataset.title   = d.title;
    item.dataset.date    = stamp;
    item.dataset.ref     = d.ref;
    item.dataset.after   = d.after;

    item.innerHTML = `
        <div class="notification-icon ${isIn ? 'info' : 'success'}">
            <svg aria-hidden="true" stroke-width="2"><use href="${isIn ? '#icon-info' : '#icon-bell'}"></use></svg>
        </div>
        <div class="notification-content">
            <p class="notification-title">${title}</p>
            <p class="notification-meta">${stamp}</p>
        </div>
        <div class="status-indicator unread-dot"></div>
    `;

    notifList.insertAdjacentElement('afterbegin', item);
    updateNotifCount();
}

function addAlert(text) {
    if (!notifList || !text) return;
    const now = new Date();
    const stamp = `${now.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })} • ` +
                  now.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });

    const item = document.createElement('div');
    item.className = 'notification-item unread';
    item.dataset.action = 'balance';   // clicking opens the balance modal
    item.innerHTML = `
        <div class="notification-icon warning">
            <svg aria-hidden="true" stroke-width="2"><use href="#icon-bell"></use></svg>
        </div>
        <div class="notification-content">
            <p class="notification-title"></p>
            <p class="notification-meta">${stamp}</p>
        </div>
        <div class="status-indicator unread-dot"></div>
    `;
    item.querySelector('.notification-title').textContent = text;

    notifList.insertAdjacentElement('afterbegin', item);
    updateNotifCount();
}


function openNotification(item) {
    const action = item.dataset.action;
    if (action === 'receipt') {
        openReceipt(item);
    } else if (action === 'balance') {
        openBalanceModal();          // was: openModal('balance-modal')
    } else {
        openModal('history-modal');
    }
}
/* clicking a notification in the drawer */
notifList?.addEventListener('click', e => {
    const item = e.target.closest('.notification-item');
    if (!item) return;

    markItemRead(item);
    setNotifOpen(false);
    openNotification(item);
});

/* bell, close button, backdrop, Esc key */
bellBtn?.addEventListener('click', e => {
    e.stopPropagation();
    setNotifOpen(!notifDropdown.classList.contains('show'));
});
notifClose?.addEventListener('click', () => setNotifOpen(false));
notifBackdrop?.addEventListener('click', () => setNotifOpen(false));
document.addEventListener('keydown', e => {
    if (e.key === 'Escape') setNotifOpen(false);
});

markAllBtn?.addEventListener('click', () => {
    notifList?.querySelectorAll('.notification-item.unread').forEach(markItemRead);
});

/* view all notifications */
notifViewAll?.addEventListener('click', e => {
    e.preventDefault();
    setNotifOpen(false);

    if (allNotifList && notifList) {
        allNotifList.innerHTML = notifList.innerHTML;
        if (!allNotifList.children.length) {
            allNotifList.innerHTML = '<p class="notif-empty">No notifications yet.</p>';
        }
    }
    openModal('notifications-modal');
});

/* clicking a notification inside the "all notifications" modal */
allNotifList?.addEventListener('click', e => {
    const item = e.target.closest('.notification-item');
    if (!item) return;

    // the modal shows a copy, so mark the matching original as read too
    const original = notifList.children[[...allNotifList.children].indexOf(item)];
    markItemRead(original);
    item.classList.remove('unread');
    item.querySelector('.unread-dot')?.remove();

    openNotification(item);
});

$('notifModalClose')?.addEventListener('click', () => $('notifications-modal')?.close());

/* right panel */
function renderPanel() {
    const card = selectedCard();
    if (!card) return;
    document.querySelector('.new-tx h2').textContent = card.dataset.name;
    document.querySelector('.chip').textContent = `•••• ${card.dataset.last4}`;
    submitLabel.textContent = selectedType() === 'deposit' ? 'Deposit funds' : 'Withdraw funds';
    $('limits-today').textContent = card.dataset.limits;
    $('overdraft-note').hidden = card.dataset.overdraft !== 'true';
}

document.querySelectorAll('input[name="account"], input[name="tx-type"]').forEach(radio =>
    radio.addEventListener('change', () => { clearMessage(); renderPanel(); })
);

/* modals */
function openModal(id) {
    const modal = $(id);
    if (modal && !modal.open) modal.showModal();
}
function openBalanceModal() {
    const set = (id, text) => { if ($(id)) $(id).textContent = text; };
    set('balance-total',    $('total-balance').textContent);
    set('balance-checking', document.querySelector('[data-balance="checking"]').textContent);
    set('balance-savings',  document.querySelector('[data-balance="savings"]').textContent);
    openModal('balance-modal');
}

$('balance-link').addEventListener('click', e => {
    e.preventDefault();
    openBalanceModal();
});
$('view-all-link').addEventListener('click', e => { e.preventDefault(); openModal('history-modal'); });

document.addEventListener('click', e => {
    const modal = e.target;
    if (!(modal instanceof HTMLDialogElement) || modal.id === 'legal-modal') return;
    const box = modal.getBoundingClientRect();
    const outside = e.clientX < box.left || e.clientX > box.right ||
                    e.clientY < box.top  || e.clientY > box.bottom;
    if (outside) modal.close();
});

/* receipt */
function openReceipt(row) {
    const d = row.dataset;
    const isIn = d.kind === 'in';

    $('receipt-icon').className = `receipt-icon receipt-icon--${isIn ? 'in' : 'out'}`;
    $('receipt-icon-use').setAttribute('href', isIn ? '#icon-arrow-down-left' : '#icon-arrow-up-right');
    $('receipt-amount').textContent      = d.signed;
    $('receipt-type').textContent        = d.type;
    $('receipt-account').textContent     = d.account;
    $('receipt-description').textContent = d.title;
    $('receipt-date').textContent        = d.date;
    $('receipt-ref').textContent         = d.ref;
    $('receipt-balance').textContent     = d.after;
    openModal('receipt-modal');
}

[txList, historyList].forEach(list => {
    if (!list) return;
    const open = e => {
        const row = e.target.closest('.tx');
        if (row) openReceipt(row);
    };
    list.addEventListener('click', open);
    list.addEventListener('keydown', e => {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(e); }
    });
});

document.querySelector('#print-receipt')?.addEventListener('click', () => window.print());

/* messages */
function showMessage(text, ok = false) {
    message.textContent = text;
    message.classList.toggle('is-ok', ok);
    message.hidden = false;
    amountField.classList.toggle('is-error', !ok);
}

function clearMessage() {
    message.hidden = true;
    amountField.classList.remove('is-error');
}

/* amount input */
amountInput.addEventListener('input', () => {
    let v = amountInput.value.replace(/[^\d.]/g, '');
    const [whole, ...rest] = v.split('.');
    v = rest.length ? `${whole}.${rest.join('').slice(0, 2)}` : whole;
    amountInput.value = v;
    clearMessage();
});

document.querySelectorAll('.quick-amounts button').forEach(btn =>
    btn.addEventListener('click', () => {
        amountInput.value = btn.dataset.amount;
        amountInput.focus();
        clearMessage();
    })
);

/* returned data */
function applyState(data) {
    for (const [key, acc] of Object.entries(data.accounts)) {
        document.querySelector(`[data-balance="${key}"]`).textContent   = acc.balance;
        document.querySelector(`[data-withdrawn="${key}"]`).textContent = acc.withdrawn;
        document.querySelector(`[data-meter="${key}"]`).style.width     = `${acc.meter}%`;
        $(`balance-${key}`).textContent = acc.balance;
        document.querySelector(`input[name="account"][value="${key}"]`)
                .closest('.account-card').dataset.limits = acc.limits;
    }
    $('total-balance').textContent = data.total;
    $('balance-total').textContent = data.total;

    txList.insertAdjacentHTML('afterbegin', data.rows.recent);
    while (txList.children.length > Number(txList.dataset.max)) txList.lastElementChild.remove();
    historyList.insertAdjacentHTML('afterbegin', data.rows.history);
    $('history-count').textContent = data.history_count;

    addNotification(txList.firstElementChild);
    addAlert(data.alert); 
    renderPanel();
}

/* submit */
txForm.addEventListener('submit', async e => {
    e.preventDefault();
    if (!parseFloat(amountInput.value)) return showMessage('Enter an amount.');

    const body = new FormData(txForm);
    body.append('account', selectedKey());
    body.append('type', selectedType());

    const csrfToken = getCsrfToken();
    if (!csrfToken) {
        return showMessage('Security token missing. Please refresh the page.');
    }

    submitBtn.disabled = true;
    try {
        const res  = await fetch(txForm.action, {
            method: 'POST',
            body,
            headers: { 'X-CSRFToken': csrfToken },
            credentials: 'same-origin',
        });
        const data = await res.json();
        showMessage(data.message, data.ok);
        if (!data.ok) return;

        applyState(data);
        amountInput.value = '';
        openReceipt(txList.firstElementChild);
    } catch {
        showMessage('Could not reach the server. Please try again.');
    } finally {
        submitBtn.disabled = false;
    }
});

renderPanel();
