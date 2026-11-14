'use strict'

const money = n => new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(n);

const $ = id => document.getElementById(id);
const amountInput = $("amount");
const amountField = document.querySelector(".amount-field");
const message = $("tx-message");
const txList = $("tx-list");

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

function getCookie(name){
    let cookieValue = null;
    if(document.cookie && document.cookie !== ''){
        const cookies = document.cookie.split(';');
        for(let i = 0; i < cookies.length; i++){
            const cookie = cookies[i].trim();
            if(cookie.substring(0, name.length + 1)=== (name + '=')){
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue
}

// UI input cleaner
amountInput.addEventListener("input", () => {
    let v = amountInput.value.replace(/[^\d.]/g, "");
    const [whole, ...rest] = v.split(".");
    amountInput.value = rest.length ? `${whole}.${rest.join("").slice(0, 2)}` : whole;
    clearMessage();
});

document.querySelectorAll("[data-amount]").forEach(btn => {
    btn.addEventListener("click", () => {
        amountInput.value = btn.dataset.amount;
        amountInput.focus();
        clearMessage();
    });
});

// Form submission handled by Python backend
$("tx-form").addEventListener("submit", async e => {
    e.preventDefault();

    const accountKey = document.querySelector('input[name="account"]:checked').value;
    const txType = document.querySelector('input[name="tx-type"]:checked').value;
    const amount = amountInput.value;

    try {
        const response = await fetch("/api/transaction/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie('csrftoken')           
             },
            body: JSON.stringify({ account: accountKey, type: txType, amount: amount })
        });

        const data = await response.json();

        if (!response.ok) {
            showMessage(data.error || "An error occurred.");
            return;
        }

        // Update UI with Python data
        for (const [key, acc] of Object.entries(data.accounts)) {
            document.querySelector(`[data-balance="${key}"]`).textContent = money(acc.balance);
            document.querySelector(`[data-withdrawn="${key}"]`).textContent = money(acc.withdrawn);
            document.querySelector(`[data-meter="${key}"]`).style.width = Math.min(100, (acc.withdrawn / 50000) * 100) + "%";
        }
        $("total-balance").textContent = money(data.total_balance);

        txList.innerHTML = "";
        data.transactions.forEach(tx => {
            const isIn = tx.amount > 0;
            const li = document.createElement("li");
            li.className = "tx";
            li.innerHTML = `
                <span class="icon-tile ${isIn ? "icon-tile--green" : "icon-tile--red"}" aria-hidden="true">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3" />
                    </svg>
                </span>
                <div class="tx-text">
                    <strong>${tx.title}</strong>
                    <small>${tx.date} • ${tx.account}</small>
                </div>
                <span class="tx-amount ${isIn ? "tx-amount--in" : "tx-amount--out"}">
                    ${isIn ? "+" : "-"}${money(Math.abs(tx.amount))}
                </span>`;
            txList.appendChild(li);
        });

        amountInput.value = "";
        showMessage(data.message, true);

    } catch (err) {
        showMessage("Network error. Please try again.");
    }
});