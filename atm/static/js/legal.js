(() => {
    const LEGAL = {
        terms: {
            title: "Terms of use",
            text:
                "This ATM simulator is provided for educational and demonstration purposes only. " +
                "It does not connect to a real bank, process real money, or create a banking relationship.\n\n" +
                "• Balances and transactions reset when the server restarts.\n" +
                "• Do not use this simulator to collect or test real card or account information.",
        },
        privacy: {
            title: "Privacy",
            text:
                "This simulator does not collect or store personal or banking information beyond your current session. " +
                "Never enter your real PIN or account details.\n\n" +
                "• All names, balances, and card numbers are fictional.\n" +
                "• Session data is cleared when you lock your session or close the browser.",
        },
        security: {
            title: "Security",
            text:
                "All data in this simulation is fictional. Real banks will never ask you to share your PIN.\n\n" +
                "• Your PIN locks after 4 incorrect attempts.\n" +
                "• Always cover the keypad and never share your PIN or card.\n" +
                "• Lock your session when you step away from the ATM.",
        },
        status: {
            title: "Status",
            text:
                "All simulator systems are operating normally.\n\n" +
                "• Card & PIN verification: Operational\n" +
                "• Deposits & withdrawals: Operational\n" +
                "• Notifications: Operational\n\n" +
                "This status page is part of the simulation and reflects no real service.",
        },
        docs: {
            title: "Docs",
            text:
                "How to use this simulator:\n\n" +
                "• Enter the PIN (1234) to access your accounts. You have 4 attempts before the PIN locks.\n" +
                "• Choose Checking or Savings, then pick Deposit or Withdrawal and enter an amount.\n" +
                "• Daily withdrawal limit: ₱50,000 per account.\n" +
                "• Checking must keep a minimum balance of ₱500.\n" +
                "• Withdrawals higher than your balance are declined.\n" +
                "• Check the bell icon for transaction alerts and low-balance warnings.",
        },
        contact: {
            title: "Contact",
            text:
                "Need help with this simulator? Reach the project team:\n\n" +
                "• Customer Hotline: " +
                '<span data-copy="09-168-239-202" style="cursor:pointer;font-weight:600;" title="Click to copy">09-168-239-202</span>\n'+
                "• Email Support: " +
                '<a href="mailto:support@abc-bank.com" style="color:inherit;text-decoration:none;font-weight:600;" title="Send email">support@abc-bank.com</a>\n' +
                "• Headquarters: ABC Financial Tower (IT Park), Cebu\n\n" +
                "Contact details are for demonstration only.",
        },
    };

    /* open a legal popup from any [data-legal] link */
    document.addEventListener("click", e => {
        const link = e.target.closest("[data-legal]");
        if (!link) return;

        e.preventDefault();

        const modal = document.getElementById("legal-modal");
        const title = document.getElementById("legal-title");
        const body  = document.getElementById("legal-body");
        const item  = LEGAL[link.dataset.legal];

        if (!modal || !item) {
            console.warn("Legal modal or content not found");
            return;
        }

        title.textContent = item.title;
        body.innerHTML = item.text;   // content above is static and trusted
        modal.showModal();
    });

    /* click-to-copy inside the popup (e.g. the hotline number) */
    document.addEventListener("click", async e => {
        const el = e.target.closest("[data-copy]");
        if (!el) return;

        const original = el.textContent;
        try {
            await navigator.clipboard.writeText(el.dataset.copy);
            el.textContent = "Copied!";
        } catch {
            el.textContent = "Copy failed";
        }
        setTimeout(() => { el.textContent = original; }, 1200);
    });

    /* click outside the popup to close it */
    document.addEventListener("click", e => {
        const modal = document.getElementById("legal-modal");
        if (modal && e.target === modal) modal.close();
    });
})();
