(() => {
    console.log("legal.js loaded");

    const LEGAL = {
        terms:    { title: "Terms of use", text: "This ATM simulator is provided for educational and demonstration purposes only. It does not connect to a real bank, process real money, or create a banking relationship." },
        privacy:  { title: "Privacy",      text: "This simulator does not collect or store personal or banking information. Never enter your real PIN or account details." },
        security: { title: "Security",     text: "All data in this simulation is fictional. Real banks will never ask you to share your PIN." },
        status:   { title: "Status",       text: "All simulator systems are operating normally." },
        docs:     { title: "Docs",         text: "Documentation for this educational simulator is coming soon." },
    contact:  { 
            title: "Contact",      
            text: `Need immediate assistance with your account or transactions? Our customer support team is available around the clock.

            • Customer Hotline: <span onclick="navigator.clipboard.writeText('(+63) 32 888-5555'); alert('Hotline number copied to clipboard!');" style="cursor: pointer; font-weight: 600;" title="Click to copy">(+63) 32 888-5555</span> / <span onclick="navigator.clipboard.writeText('1-800-10-ABC-BANK'); alert('Hotline number copied to clipboard!');" style="cursor: pointer; font-weight: 600;" title="Click to copy">1-800-10-ABC-BANK</span>
            • Email Support: <a href="mailto:support@abc-bank.com.ph" style="color: inherit; text-decoration: none; font-weight: 600;" title="Send email">support@abc-bank.com.ph</a>
            • Headquarters: ABC Financial Tower, Lapu-Lapu / Mandaue City, Cebu` 
        }

    }
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
        body.innerHTML = item.text;
        modal.showModal();
    });

    document.addEventListener("click", e => {
        const modal = document.getElementById("legal-modal");
        if (modal && e.target === modal) modal.close();
    });
})();