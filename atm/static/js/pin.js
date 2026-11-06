const CORRECT_PIN  = "1234";   // simulator only
const PIN_LENGTH   = 4;
const MAX_ATTEMPTS = 4;

let pin = "";
let attempts = MAX_ATTEMPTS;
let locked = false;

const form        = document.getElementById("pin-form");
const field       = document.getElementById("pin-field");
const dots        = document.querySelectorAll(".dot");
const count       = document.getElementById("pin-count");
const errorEl     = document.getElementById("pin-error");
const errorText   = document.getElementById("pin-error-text");
const metaEl      = document.getElementById("pin-meta");
const attemptsEl  = document.getElementById("attempts");
const keys        = document.querySelectorAll(".key");
const lockBtn     = document.getElementById("lock-btn");
const cardDesc    = document.querySelector(".card-desc");
const submitBtn   = document.getElementById("submit-btn");
const submitLabel = document.getElementById("submit-label");

const DEFAULT_DESC = cardDesc.textContent;

/* ---------- display ---------- */
function render() {
    dots.forEach((dot, i) => dot.classList.toggle("filled", i < pin.length));
    count.textContent = `${pin.length}/${PIN_LENGTH}`;
    field.classList.toggle("is-active", pin.length > 0 && !locked);
}

function showError(message) {
    errorText.textContent = message;
    errorEl.hidden = false;
    metaEl.hidden = true;
    field.classList.add("is-error");
    field.classList.remove("is-active");
}

function clearError() {
    errorEl.hidden = true;
    metaEl.hidden = false;
    field.classList.remove("is-error");
}

function updateAttempts() {
    attemptsEl.textContent = `${attempts} attempt${attempts === 1 ? "" : "s"} left`;
}

/* ---------- lock / unlock ---------- */
function lockPin() {
    locked = true;
    pin = "";
    render();

    keys.forEach(k => (k.disabled = true));
    submitBtn.disabled = true;
    submitLabel.textContent = "PIN access locked";

    lockBtn.disabled = false;
    lockBtn.classList.add("is-locked");
    lockBtn.setAttribute("aria-label", "Unlock the simulator");

    cardDesc.textContent = "PIN access is locked. Tap the red lock icon to unlock this simulator.";
    showError("PIN locked after four incorrect attempts. Tap the red lock icon to unlock.");
    field.classList.remove("is-error");
    field.classList.add("is-locked");
}

function unlockPin() {
    locked = false;
    attempts = MAX_ATTEMPTS;
    pin = "";

    keys.forEach(k => (k.disabled = false));
    submitBtn.disabled = false;
    submitLabel.textContent = "Access my accounts";

    lockBtn.disabled = true;
    lockBtn.classList.remove("is-locked");
    lockBtn.setAttribute("aria-label", "PIN lock status");

    cardDesc.textContent = DEFAULT_DESC;
    field.classList.remove("is-locked");
    clearError();
    updateAttempts();
    render();
}

/* ---------- input ---------- */
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
    pin = "";
    render();
}

// on-screen keypad
keys.forEach(key => {
    key.addEventListener("click", () => {
        const value = key.dataset.key;
        if (value === "clear") clearPin();
        else if (value === "back") removeDigit();
        else addDigit(value);
    });
});

// physical keyboard
document.addEventListener("keydown", e => {
    if (locked) return;

    if (e.key >= "0" && e.key <= "9") {
        addDigit(e.key);
    } else if (e.key === "Backspace") {
        removeDigit();
    } else if (e.key === "Escape") {
        clearPin();
    } else if (e.key === "Enter") {
        // stop Enter from "clicking" a focused keypad button
        e.preventDefault();
        form.requestSubmit();
    }
});

// red lock button unlocks
lockBtn.addEventListener("click", () => {
    if (locked) unlockPin();
});

/* ---------- submit ---------- */
form.addEventListener("submit", e => {
    e.preventDefault();
    if (locked) return;

    if (pin.length < PIN_LENGTH) {
        showError("Please enter all four digits.");
        return;
    }

    if (pin === CORRECT_PIN) {
        // TODO: replace with your dashboard URL, e.g. "/dashboard/"
        alert("PIN correct! Redirect to your dashboard here.");
        return;
    }

    attempts -= 1;
    pin = "";
    render();
    updateAttempts();

    if (attempts === 0) {
        lockPin();
    } else {
        showError(`Incorrect PIN. ${attempts} attempt${attempts === 1 ? "" : "s"} remaining.`);
    }
});

render();
updateAttempts();