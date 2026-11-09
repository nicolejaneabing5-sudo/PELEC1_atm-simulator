(() => {
    console.log("legal.js loaded");

    const LEGAL = {
        terms:    { title: "Terms of use", text: "This ATM simulator is provided for educational and demonstration purposes only. It does not connect to a real bank, process real money, or create a banking relationship." },
        privacy:  { title: "Privacy",      text: "This simulator does not collect or store personal or banking information. Never enter your real PIN or account details." },
        security: { title: "Security",     text: "All data in this simulation is fictional. Real banks will never ask you to share your PIN." },
        status:   { title: "Status",       text: "All simulator systems are operating normally." },
        docs:     { title: "Docs",         text: "Documentation for this educational simulator is coming soon." },
        contact:  { title: "Contact",      text: "This is a demo project, so there is no real support desk to contact." }
    };

    document.addEventListener("click", e => {
        const link = e.target.closest("[data-legal]");
        if (!link) return;

        e.preventDefault();   // stops the jump to the top

        const modal = document.getElementById("legal-modal");
        const title = document.getElementById("legal-title");
        const body  = document.getElementById("legal-body");
        const item  = LEGAL[link.dataset.legal];

        if (!modal || !item) {
            console.warn("Legal modal or content not found");
            return;
        }

        title.textContent = item.title;
        body.textContent = item.text;
        modal.showModal();
    });

    // clicking the dark backdrop closes the modal
    document.addEventListener("click", e => {
        const modal = document.getElementById("legal-modal");
        if (modal && e.target === modal) modal.close();
    });
})();