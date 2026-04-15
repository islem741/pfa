document.addEventListener('DOMContentLoaded', function() {
    // Initialisation du calendrier
    initCalendar();
    
    // Gestion des vues (calendrier/liste)
    setupViewToggle();
    
    // Gestion des filtres
    setupFilters();
    
    // Gestion du modal
    setupModal();
});

function initCalendar() {
    const calendarEl = document.getElementById('calendar');
    
    const calendar = new FullCalendar.Calendar(calendarEl, {
        locale: 'fr',
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        buttonText: {
            today: 'Aujourd\'hui',
            month: 'Mois',
            week: 'Semaine',
            day: 'Jour'
        },
        events: [
            {
                title: 'Consultation Dr. Martin',
                start: '2023-11-15T14:30:00',
                end: '2023-11-15T15:15:00',
                backgroundColor: '#29d9d5',
                borderColor: '#29d9d5',
                extendedProps: {
                    status: 'upcoming',
                    expert: 'Dr. Sophie Martin',
                    type: 'video'
                }
            },
            {
                title: 'Appel Me. Dupont',
                start: '2023-11-10T10:00:00',
                end: '2023-11-10T11:00:00',
                backgroundColor: '#2ecc71',
                borderColor: '#2ecc71',
                extendedProps: {
                    status: 'completed',
                    expert: 'Me. Jean Dupont',
                    type: 'phone'
                }
            }
        ],
        eventClick: function(info) {
            showAppointmentDetails(info.event);
        }
    });
    
    calendar.render();
}

function setupViewToggle() {
    const viewOptions = document.querySelectorAll('.view-option');
    const views = document.querySelectorAll('.appointment-view');
    
    viewOptions.forEach(option => {
        option.addEventListener('click', function() {
            // Active le bouton sélectionné
            viewOptions.forEach(opt => opt.classList.remove('active'));
            this.classList.add('active');
            
            // Affiche la vue correspondante
            const viewName = this.dataset.view;
            views.forEach(view => view.classList.remove('active-view'));
            document.getElementById(`${viewName}-view`).classList.add('active-view');
        });
    });
}

function setupFilters() {
    const statusFilter = document.getElementById('status-filter');
    const expertFilter = document.getElementById('expert-filter');
    const resetBtn = document.getElementById('reset-filters');
    
    // Filtrage des RDV
    function filterAppointments() {
        const status = statusFilter.value;
        const expert = expertFilter.value;
        
        document.querySelectorAll('.appointment-item').forEach(item => {
            const itemStatus = item.classList.contains('upcoming') ? 'upcoming' : 
                              item.classList.contains('completed') ? 'completed' : 'canceled';
            const itemExpert = item.querySelector('.specialty').textContent.toLowerCase();
            
            const statusMatch = status === 'all' || itemStatus === status;
            const expertMatch = expert === 'all' || itemExpert.includes(expert);
            
            if (statusMatch && expertMatch) {
                item.style.display = 'block';
            } else {
                item.style.display = 'none';
            }
        });
    }
    
    statusFilter.addEventListener('change', filterAppointments);
    expertFilter.addEventListener('change', filterAppointments);
    
    resetBtn.addEventListener('click', function() {
        statusFilter.value = 'all';
        expertFilter.value = 'all';
        filterAppointments();
    });
}

function setupModal() {
    const modal = document.getElementById('appointment-modal');
    const openBtn = document.getElementById('new-appointment-btn');
    const closeBtns = document.querySelectorAll('.close-modal');
    const form = document.getElementById('new-appointment-form');
    
    // Ouvrir le modal
    openBtn.addEventListener('click', function() {
        modal.style.display = 'block';
    });
    
    // Fermer le modal
    closeBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            modal.style.display = 'none';
        });
    });
    
    // Fermer quand on clique en dehors
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
    
    // Gestion du formulaire
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Ici, vous ajouteriez la logique pour enregistrer le nouveau RDV
        const expert = document.getElementById('expert-select').value;
        const type = document.getElementById('appointment-type').value;
        const date = document.getElementById('appointment-date').value;
        const time = document.getElementById('appointment-time').value;
        const notes = document.getElementById('appointment-notes').value;
        
        console.log('Nouveau RDV:', { expert, type, date, time, notes });
        
        // Afficher un message de confirmation
        alert('Votre rendez-vous a été programmé avec succès!');
        
        // Fermer le modal et réinitialiser le formulaire
        modal.style.display = 'none';
        form.reset();
    });
}

function showAppointmentDetails(event) {
    const title = event.title;
    const start = event.start;
    const end = event.end;
    const status = event.extendedProps.status;
    const expert = event.extendedProps.expert;
    const type = event.extendedProps.type;
    
    // Formatage de la date et heure
    const options = { 
        weekday: 'long', 
        day: 'numeric', 
        month: 'long', 
        year: 'numeric',
        hour: '2-digit', 
        minute: '2-digit' 
    };
    
    const startStr = start.toLocaleDateString('fr-FR', options);
    const endStr = end.toLocaleDateString('fr-FR', { hour: '2-digit', minute: '2-digit' });
    
    // Création du message de détail
    let message = `
        <h4>${title}</h4>
        <p><strong>Expert:</strong> ${expert}</p>
        <p><strong>Date:</strong> ${startStr} - ${endStr}</p>
        <p><strong>Type:</strong> ${type === 'video' ? 'Visioconférence' : 'Appel téléphonique'}</p>
        <p><strong>Statut:</strong> ${status === 'upcoming' ? 'À venir' : 'Terminé'}</p>
    `;
    
    // Affichage dans une boîte de dialogue (pourrait être remplacé par un modal plus joli)
    alert(message.replace(/<[^>]*>/g, ''));
}
