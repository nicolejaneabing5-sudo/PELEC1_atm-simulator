'use strict';

/* =========================================================
   dashboard.js — interface behavior only.
   Python (views.py + atm/oop/domain.py) owns every balance, limit and rule.
   JS reads text from the page (data-* attributes) and writes back what Python returns.
   ========================================================= */

/* ---------- elements ---------- */
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

/* ---------- greeting (name comes from Python via data-name) ---------- */
const greeting = $('greeting-title');
const hour = new Date().getHours();
greeting.textContent =
    `Good ${hour < 12 ? 'morning' : hour < 18 ? 'afternoon' : 'evening'}, ${greeting.dataset.name}`;

/* ---------- right-hand panel follows the selected account / type ---------- */
function renderPanel() {
    const card = selectedCard();
    document.querySelector('.new-tx h2').textContent = card.dataset.name;
    document.querySelector('.chip').textContent = `•••• ${card.dataset.last4}`;
    submitLabel.textContent = selectedType() === 'deposit' ? 'Deposit funds' : 'Withdraw funds';
    $('limits-today').textContent = card.dataset.limits;
    $('overdraft-note').hidden = card.dataset.overdraft !== 'true';
}

document.querySelectorAll('input[name="account"], input[name="tx-type"]').forEach(radio =>
    radio.addEventListener('change', () => { clearMessage(); renderPanel(); })
);

/* ---------- popups ---------- */
function openModal(id) {
    const modal = $(id);
    if (modal && !modal.open) modal.showModal();
}

$('balance-link').addEventListener('click', e => { e.preventDefault(); openModal('balance-modal'); });
$('view-all-link').addEventListener('click', e => { e.preventDefault(); openModal('history-modal'); });

// clicking the dark backdrop closes a popup (legal.js handles the legal one)
document.addEventListener('click', e => {
    const modal = e.target;
    if (!(modal instanceof HTMLDialogElement) || modal.id === 'legal-modal') return;
    const box = modal.getBoundingClientRect();
    const outside = e.clientX < box.left || e.clientX > box.right ||
                    e.clientY < box.top  || e.clientY > box.bottom;
    if (outside) modal.close();
});

/* ---------- receipt: filled from the clicked row's data-* attributes ---------- */
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

// click, Enter or Space on a row opens its receipt (no server request needed)
[txList, historyList].forEach(list => {
    const open = e => {
        const row = e.target.closest('.tx');
        if (row) openReceipt(row);
    };
    list.addEventListener('click', open);
    list.addEventListener('keydown', e => {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(e); }
    });
});

/* ---------- messages ---------- */
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

/* ---------- amount input: digits and one dot, max 2 decimals ---------- */
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

/* ---------- show what Python returned ---------- */
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

    // new row on top of both lists (HTML is rendered by Python); dashboard list stays short
    txList.insertAdjacentHTML('afterbegin', data.rows.recent);
    while (txList.children.length > Number(txList.dataset.max)) txList.lastElementChild.remove();
    historyList.insertAdjacentHTML('afterbegin', data.rows.history);
    $('history-count').textContent = data.history_count;

    renderPanel();
}

/* ---------- submit: the only request this page makes ---------- */
txForm.addEventListener('submit', async e => {
    e.preventDefault();
    if (!parseFloat(amountInput.value)) return showMessage('Enter an amount.');

    const body = new FormData(txForm);      // amount + csrf token
    body.append('account', selectedKey());
    body.append('type', selectedType());

    submitBtn.disabled = true;
    try {
        const res  = await fetch(txForm.action, { method: 'POST', body });
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