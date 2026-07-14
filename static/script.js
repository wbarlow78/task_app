const cards = document.querySelectorAll(".task-card");

cards.forEach(function(card) {
    card.addEventListener("mouseenter", function() {
        card.classList.add("task-hover");
    });

    card.addEventListener("mouseleave", function() {
        card.classList.remove("task-hover");
    });
});

const toggleForms = document.querySelectorAll(".toggle-form");

toggleForms.forEach(function(form) {
    form.addEventListener("submit", function(event) {
        event.preventDefault();

        const taskCard = form.closest(".task-card");

        taskCard.classList.remove("task-hover");
        taskCard.classList.add("task-fade-out");

        setTimeout(function() {
            form.submit();
        }, 500);
    });
});

const deleteLinks = document.querySelectorAll(".delete-link");

deleteLinks.forEach(function(link) {
    link.addEventListener("click", function(event) {
        event.preventDefault();

        const confirmed = confirm(
            "Are you sure you want to delete this task?"
        );

        if (!confirmed) {
            return;
        }

        const taskCard = link.closest(".task-card");

        taskCard.classList.remove("task-hover");
        taskCard.classList.add("task-fade-out");

        setTimeout(function() {
            window.location.href = link.href;
        }, 500);
    });
});

const flash = document.querySelector(".flash-message"); 

if (flash) {
    setTimeout(function() {
        flash.remove();
    }, 3000);
} 
