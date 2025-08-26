const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))

const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]')
const popoverList = [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl))


const nav = document.querySelector('.navbar-collapse')

document.addEventListener('click', () => {
    if (nav.classList.contains('show')) {
        nav.classList.remove('show')
    }
})


document.addEventListener("DOMContentLoaded", function () {
    const errorMessages = [
        "Doctor, heal thyself. The admin panel needs a hug.",
        "Well, this escalated quickly. Error 500 has entered the chat.",
        "The server tripped over its own code. Please stand by.",
        "Even the backend needs a coffee break sometimes ☕.",
        "Error 500: The system is currently questioning its life choices.",
        "Oops! Something broke. You're the admin, so... good luck!",
        "The server is down. Probably watching cat videos again.",
        "500 Internal Server Error. Have you tried turning it off and on again?",
        "This is fine 🔥. Everything is fine.",
        "Congratulations! You've unlocked the rare and majestic Error 500."
    ]

    function getRandomErrorMessage() {
        const index = Math.floor(Math.random() * errorMessages.length);
        return errorMessages[index];
    }


    function showError500() {
        const message = getRandomErrorMessage();
        console.error(message);
        document.getElementById("error-text").innerText = message;
    }

    showError500()
})


document.querySelector('form').addEventListener('submit', function(e) {
    const btn = this.querySelector('button[type="submit"]');
    btn.disabled = true;
    btn.innerText = 'Uploading...';
  });


setTimeout(() => {
    document.querySelectorAll('.flash-overlay .alert').forEach(alert => {
        alert.classList.add('fade-out');
        setTimeout(() => alert.remove(), 500);
    });
}, 3000);

