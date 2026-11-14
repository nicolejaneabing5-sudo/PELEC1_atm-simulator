// Expose card insertion globally so inline onclick works
window.triggerCardInsertion = function () {
    const card = document.getElementById("debit-card");
    const slotMouth = document.getElementById("card-slot-mouth");
    const btn = document.getElementById("insert-btn");
    const statusHint = document.getElementById("status-hint");
    const slotLight = document.getElementById("slot-light");

    if (!card || card.classList.contains("inserted")) return;

    btn.disabled = true;
    btn.textContent = "Reading card...";
    if (statusHint) statusHint.textContent = "Processing card, please wait...";
    if (slotLight) slotLight.classList.add("reading");

    // Animate card going into slot
    card.style.transition = "transform 0.75s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.5s ease";
    card.classList.add("inserted");
    if (slotMouth) slotMouth.classList.remove("highlight-drop");

    // Redirect after animation completes
    setTimeout(() => {
        window.location.href = "/pin/";
    }, 900);
};

document.addEventListener("DOMContentLoaded", () => {
    const card = document.getElementById("debit-card");
    const slotMouth = document.getElementById("card-slot-mouth");

    if (!card) return;

    let isDragging = false;
    let startY = 0;

    // Pointer Down (Mouse or Touch)
    card.addEventListener("pointerdown", (e) => {
        if (card.classList.contains("inserted")) return;
        isDragging = true;
        startY = e.clientY;
        card.setPointerCapture(e.pointerId);
        card.style.transition = "none";
    });

    // Pointer Move
    card.addEventListener("pointermove", (e) => {
        if (!isDragging || card.classList.contains("inserted")) return;

        const deltaY = e.clientY - startY;

        if (deltaY < 30) {
            card.style.transform = `translateY(${deltaY}px)`;
        }

        if (slotMouth) {
            const mouthRect = slotMouth.getBoundingClientRect();
            const cardRect = card.getBoundingClientRect();

            if (cardRect.top <= mouthRect.bottom + 25) {
                slotMouth.classList.add("highlight-drop");
            } else {
                slotMouth.classList.remove("highlight-drop");
            }
        }
    });

    // Pointer Up
    card.addEventListener("pointerup", (e) => {
        if (!isDragging || card.classList.contains("inserted")) return;
        isDragging = false;

        if (slotMouth) {
            const mouthRect = slotMouth.getBoundingClientRect();
            const cardRect = card.getBoundingClientRect();

            if (cardRect.top <= mouthRect.bottom + 15) {
                window.triggerCardInsertion();
            } else {
                card.style.transition = "transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)";
                card.style.transform = "translateY(0px)";
                slotMouth.classList.remove("highlight-drop");
            }
        }
    });
});