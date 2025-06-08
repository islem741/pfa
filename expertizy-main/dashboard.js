document.addEventListener('DOMContentLoaded', function() {
    // Gestion des notifications
    const notificationBell = document.querySelector('.notifications');
    if (notificationBell) {
        notificationBell.addEventListener('click', function() {
            alert("Affichage des notifications");
            // Ici vous pourriez afficher une modal avec les notifications
        });
    }

    // Gestion des boutons d'annulation
    const cancelButtons = document.querySelectorAll('.btn-cancel');
    cancelButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            if (confirm("Êtes-vous sûr de vouloir annuler ce rendez-vous ?")) {
                // Logique d'annulation
                const appointmentCard = this.closest('.appointment-card');
                appointmentCard.style.opacity = '0.5';
                this.textContent = 'Annulation en cours...';
                this.disabled = true;
                
                // Simulation d'une requête asynchrone
                setTimeout(() => {
                    appointmentCard.remove();
                    alert("Rendez-vous annulé avec succès");
                }, 1500);
            }
        });
    });

    // Gestion des boutons de notation
    const rateButtons = document.querySelectorAll('.btn-small:first-child');
    rateButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const expertName = this.closest('tr').querySelector('td:nth-child(2)').textContent;
            alert(`Ouverture du formulaire de notation pour ${expertName}`);
        });
    });

    // Animation des cartes d'action
    const actionCards = document.querySelectorAll('.action-card');
    actionCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.querySelector('i').style.transform = 'scale(1.1)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.querySelector('i').style.transform = 'scale(1)';
        });
    });
});