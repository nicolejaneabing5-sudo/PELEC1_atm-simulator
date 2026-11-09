'use strict'

const LIMIT_PER_TX = 25000;
const LIMIT_DAILY  = 50000;
const OVERDRAFT    = 500;   // checking only

const accounts = {
    checking: { name: "Checking Account", last4: "4821", balance: 8240.50,  withdrawn: 0, overdraft: true  },
    savings:  { name: "Savings Account",  last4: "9017", balance: 12860.22, withdrawn: 0, overdraft: false }
};

const transactions = [
    { title: "Payroll deposit", date: "Apr 24, 2025", account: "Checking", amount:  2450 },
    { title: "ATM withdrawal",  date: "Apr 22, 2025", account: "Checking", amount:  -100 },
    { title: "Monthly savings", date: "Apr 21, 2025", account: "Savings",  amount:   750 },
    { title: "Cash deposit",    date: "Apr 18, 2025", account: "Checking", amount:   480 }
];

const money = n => new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(n);

/* ---------- elements ---------- */
const $ = id => document.getElementById(id);
const accountRadios = document.querySelectorAll('input[name="account"]');
const typeRadios    = document.querySelectorAll('input[name="tx-type"]');
const txForm        = $("tx-form");
const amountInput   = $("amount");
const amountField   = document.querySelector(".amount-field");
const message       = $("tx-message");
const submitLabel   = $("tx-submit-label");
const txList        = $("tx-list");

const selectedKey  = () => document.querySelector('input[name="account"]:checked').value;
const selectedType = () => document.querySelector('input[name="tx-type"]:checked').value;

/* ---------- greeting ---------- */
const hour = new Date().getHours();
$("greeting-title").textContent =
    `Good ${hour < 12 ? "morning" : hour < 18 ? "afternoon" : "evening"}, Jordan`;

/* ---------- render ---------- */
const ICON_IN  = "M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3";
const ICON_OUT = "M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5";

function renderAccounts() {
    let total = 0;
    for (const [key, acc] of Object.entries(accounts)) {
        total += acc.balance;
        document.querySelector(`[data-balance="${key}"]`).textContent = money(acc.balance);
        document.querySelector(`[data-withdrawn="${key}"]`).textContent = money(acc.withdrawn);
        document.querySelector(`[data-meter="${key}"]`).style.width =
            Math.min(100, (acc.withdrawn / LIMIT_DAILY) * 100) + "%";
    }
    $("total-balance").textContent = money(total);
}

function renderPanel() {
    const acc = accounts[selectedKey()];
    const type = selectedType();

    document.querySelector(".new-tx h2").textContent = acc.name;
    document.querySelector(".chip").textContent = `•••• ${acc.last4}`;
    submitLabel.textContent = type === "deposit" ? "Deposit funds" : "Withdraw funds";

    $("limits-today").textContent =
        `Withdrawn today: ${money(acc.withdrawn)} • ${money(LIMIT_DAILY - acc.withdrawn)} remaining`;
    $("overdraft-note").hidden = !acc.overdraft;
}

function renderTransactions() {
    txList.innerHTML = "";
    transactions.forEach(tx => {
        const isIn = tx.amount > 0;
        const li = document.createElement("li");
        li.className = "tx";
        li.innerHTML = `
            <span class="icon-tile ${isIn ? "icon-tile--green" : "icon-tile--red"}" aria-hidden="true">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" d="${isIn ? ICON_IN : ICON_OUT}" />
                </svg>
            </span>
            <div class="tx-text">
                <strong></strong>
                <small>${tx.date} • ${tx.account}</small>
            </div>
            <span class="tx-amount ${isIn ? "tx-amount--in" : "tx-amount--out"}">
                ${isIn ? "+" : "-"}${money(Math.abs(tx.amount))}
            </span>`;
        li.querySelector("strong").textContent = tx.title;
        txList.appendChild(li);
    });
}

/* ---------- messages ---------- */
function showMessage(text, ok = false) {
    message.textContent = text;
    message.classList.toggle("is-ok", ok);
    message.hidden = false;
    amountField.classList.toggle("is-error", !ok);
}

function clearMessage() {
    message.hidden = true;
    amountField.classList.remove("is-error");
}

/* ---------- amount input: digits and one dot, max 2 decimals ---------- */
amountInput.addEventListener("input", () => {
    let v = amountInput.value.replace(/[^\d.]/g, "");
    const [whole, ...rest] = v.split(".");
    v = rest.length ? `${whole}.${rest.join("").slice(0, 2)}` : whole;
    amountInput.value = v;
    clearMessage();
});

document.querySelectorAll("[data-amount]").forEach(btn => {
    btn.addEventListener("click", () => {
        amountInput.value = btn.dataset.amount;
        amountInput.focus();
        clearMessage();
    });
});

/* ---------- selection changes ---------- */
accountRadios.forEach(r => r.addEventListener("change", () => { clearMessage(); renderPanel(); }));
typeRadios.forEach(r => r.addEventListener("change", () => { clearMessage(); renderPanel(); }));

/* ---------- submit ---------- */
txForm.addEventListener("submit", e => {
    e.preventDefault();

    const key = selectedKey();
    const acc = accounts[key];
    const type = selectedType();
    const amount = Math.round(parseFloat(amountInput.value) * 100) / 100;

    if (!amount || amount <= 0) {
        showMessage("Enter an amount greater than $0.00.");
        return;
    }

    if (type === "withdrawal") {
        if (amount > LIMIT_PER_TX) {
            showMessage(`The limit is ${money(LIMIT_PER_TX)} per transaction.`);
            return;
        }
        if (acc.withdrawn + amount > LIMIT_DAILY) {
            showMessage(`This exceeds your daily limit. ${money(LIMIT_DAILY - acc.withdrawn)} remaining.`);
            return;
        }
        const available = acc.balance + (acc.overdraft ? OVERDRAFT : 0);
        if (amount > available) {
            showMessage("Insufficient funds for this withdrawal.");
            return;
        }
        acc.balance -= amount;
        acc.withdrawn += amount;
    } else {
        acc.balance += amount;
    }

    transactions.unshift({
        title: type === "deposit" ? "Cash deposit" : "ATM withdrawal",
        date: new Date().toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }),
        account: key === "checking" ? "Checking" : "Savings",
        amount: type === "deposit" ? amount : -amount
    });

    amountInput.value = "";
    renderAccounts();
    renderPanel();
    renderTransactions();
    showMessage(`${type === "deposit" ? "Deposited" : "Withdrew"} ${money(amount)} successfully.`, true);
});

renderAccounts();
renderPanel();
renderTransactions();