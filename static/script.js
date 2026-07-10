const cards = document.querySelectorAll(".task-card");

cards.forEach(function(card) {
    card.addEventListener("mouseenter", function() {
        card.style.transform = "scale(1.02)";
    });

    card.addEventListener("mouseleave", function() {
        card.style.transform = "scale(1)";
    });
});