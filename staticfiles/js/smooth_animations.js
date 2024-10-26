document.addEventListener('DOMContentLoaded', function() {
    const selectElement = document.querySelector('select[name="city"]');
    selectElement.addEventListener('change', function() {
        document.body.style.opacity = '0.6';
        setTimeout(() => {
            document.body.style.opacity = '1';
        }, 300);
    });
});
// Smooth horizontal scrolling for navbar
document.querySelectorAll('.navbar a').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        document.querySelector(this.getAttribute('href')).scrollIntoView({
            behavior: 'smooth'
        });
    });
});
