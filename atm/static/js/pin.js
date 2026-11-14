'use strict';

const PIN_LENGTH = 4;   

/* Elements */
const form        = document.getElementById('pin-form');
const field       = document.getElementById('pin-field');
const input       = document.getElementById('pin-input');
const dots        = document.querySelectorAll('.dot');
const count       = document.getElementById('pin-count');
const errorEl     = document.getElementById('pin-error');
const errorText   = document.getElementById('pin-error-text');
const metaEl      = document.getElementById('pin-meta');
const attemptsEl  = document.getElementById('attempts');
const keys        = document.querySelectorAll('.key');
const lockBtn     = document.getElementById('lock-btn');
const cardDesc    = document.querySelector('.card-desc');
const submitBtn   = document.getElementById('submit-btn');
const submitLabel = document.getElementById('submit-label');

const DEFAULT_DESC = cardDesc.textContent;

/* State */
let pin = '';
let attempts = Number(form.dataset.attempts);
let locked = form.dataset.locked === 'true';


async function post(url, data = {}) {
    const body = new FormData(form);   
    Object.entries(data).forEach(([key, value]) => body.append(key, value));
    const res = await fetch(url, { method: 'POST', body });
    return res.json();
}

/* DISPLAY */
function render() {
    dots.forEach((dot, i) => {
        dot.classList.toggle('filled', i < pin.length);
        dot.classList.toggle('current', i === pin.length && !locked);
    });
    count.textContent = `${pin.length}/${PIN_LENGTH}`;
    input.value = pin;
    field.classList.toggle('is-active', pin.length > 0 && !locked);
}

function showError(message) {
    errorText.textContent = message;
    errorEl.hidden = false;
    metaEl.hidden = true;
    field.classList.add('is-error');
    field.classList.remove('is-active');
}

function clearError() {
    errorEl.hidden = true;
    metaEl.hidden = false;
    field.classList.remove('is-error');
}

function updateAttempts() {
    attemptsEl.textContent = `${attempts} attempt${attempts === 1 ? '' : 's'} left`;
}

/* Lock / Unlock */
function showLocked() {
    locked = true;
    pin = '';
    render();

    input.disabled = true;
    keys.forEach(k => (k.disabled = true));
    submitBtn.disabled = true;
    submitLabel.textContent = 'PIN access locked';

    lockBtn.disabled = false;
    lockBtn.classList.add('is-locked');
    lockBtn.setAttribute('aria-label', 'Unlock the simulator');

    cardDesc.textContent = 'PIN access is locked. Tap the red lock icon to unlock this simulator.';
    showError('PIN locked after too many incorrect attempts. Tap the red lock icon to unlock.');
    field.classList.remove('is-error');
    field.classList.add('is-locked');
}

function showUnlocked(attemptsLeft) {
    locked = false;
    attempts = attemptsLeft;
    pin = '';

    input.disabled = false;
    keys.forEach(k => (k.disabled = false));
    submitBtn.disabled = false;
    submitLabel.textContent = 'Access my accounts';

    lockBtn.disabled = true;
    lockBtn.classList.remove('is-locked');
    lockBtn.setAttribute('aria-label', 'PIN lock status');

    cardDesc.textContent = DEFAULT_DESC;
    field.classList.remove('is-locked');
    clearError();
    updateAttempts();
    render();
    input.focus({ preventScroll: true });
}

/* PIN Input */
function addDigit(d) {
    if (locked || pin.length >= PIN_LENGTH) return;
    clearError();
    pin += d;
    render();
}

function removeDigit() {
    if (locked) return;
    clearError();
    pin = pin.slice(0, -1);
    render();
}

function clearPin() {
    if (locked) return;
    clearError();
    pin = '';
    render();
}


keys.forEach(key => {
    key.addEventListener('click', () => {
        const value = key.dataset.key;
        if (value === 'clear') clearPin();
        else if (value === 'back') removeDigit();
        else addDigit(value);
    });
});


input.addEventListener('input', () => {
    if (locked) return;
    pin = input.value.replace(/\D/g, '').slice(0, PIN_LENGTH);
    clearError();
    render();
});


document.addEventListener('keydown', e => {
    if (locked || document.querySelector('dialog[open]')) return;
    if (e.ctrlKey || e.metaKey || e.altKey) return;

    if (e.key.length === 1 && e.key >= '0' && e.key <= '9') {
        e.preventDefault();          
        addDigit(e.key);
    } else if (e.key === 'Backspace') {
        e.preventDefault();
        removeDigit();
    } else if (e.key === 'Escape') {
        clearPin();
    } else if (e.key === 'Enter') {
        e.preventDefault();
        form.requestSubmit();
    }
});

/* Incorrect PIN */
lockBtn.addEventListener('click', async () => {
    if (!locked) return;
    try {
        const data = await post(lockBtn.dataset.url);
        if (data.ok) showUnlocked(data.attempts_left);
    } catch {
        showError('Could not reach the server. Please try again.');
    }
});

/* Checks PIN */
form.addEventListener('submit', async e => {
    e.preventDefault();
    if (locked) return;
    if (pin.length < PIN_LENGTH) return showError('Please enter all four digits.');

    submitBtn.disabled = true;
    try {
        const data = await post(form.action, { pin });
        if (data.ok) {
            window.location.href = data.redirect;
            return;
        }
        pin = '';
        attempts = data.attempts_left;
        render();
        updateAttempts();
        if (data.locked) showLocked();
        else showError(data.message);
    } catch {
        showError('Could not reach the server. Please try again.');
    } finally {
        if (!locked) submitBtn.disabled = false;
    }
});

/* start */
render();
updateAttempts();
if (locked) showLocked();


if (!locked && window.matchMedia('(pointer: fine)').matches) {
    input.focus({ preventScroll: true });
}