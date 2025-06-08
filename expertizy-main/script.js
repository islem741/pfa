document.addEventListener('DOMContentLoaded', function() {
    // 1. Toggle expert fields
    const accountType = document.getElementById('account-type');
    const expertFields = document.getElementById('expert-fields');
    
    if (accountType && expertFields) {
        accountType.addEventListener('change', function() {
            expertFields.style.display = this.value === 'expert' ? 'block' : 'none';
        });
    }

    // 2. Form validation
    const form = document.getElementById('signup-form');
    if (form) {
        form.addEventListener('submit', function(e) {
            let isValid = true;
            
            // Check required fields
            document.querySelectorAll('[required]').forEach(field => {
                if (!field.value.trim()) {
                    field.style.borderColor = 'red';
                    isValid = false;
                } else {
                    field.style.borderColor = '#29d9d5';
                }
            });

            // Check password match
            const password = form.querySelector('input[type="password"]');
            const confirmPassword = form.querySelectorAll('input[type="password"]')[1];
            
            if (password && confirmPassword && password.value !== confirmPassword.value) {
                confirmPassword.style.borderColor = 'red';
                isValid = false;
                alert('Les mots de passe ne correspondent pas');
            }

            if (!isValid) {
                e.preventDefault();
                alert('Veuillez remplir tous les champs obligatoires');
            }
        });
    }
});

document.addEventListener('DOMContentLoaded', function() {
    // Sélection des éléments
    const testimonialCards = document.querySelectorAll('.testimonial-card');
    const prevBtn = document.querySelector('.control-prev');
    const nextBtn = document.querySelector('.control-next');
    const dots = document.querySelectorAll('.indicator');
    const testimonialContainer = document.querySelector('.testimonial-container');
    
    // Variables de contrôle
    let currentIndex = 0;
    let isAnimating = false;
    let autoSlideInterval;
    const intervalDuration = 5000; // 5 secondes

    // Fonction pour afficher un témoignage spécifique
    function showTestimonial(index) {
        if (isAnimating) return;
        
        isAnimating = true;
        
        // Vérifier les limites
        if (index >= testimonialCards.length) index = 0;
        if (index < 0) index = testimonialCards.length - 1;
        
        // Masquer la carte actuelle
        testimonialCards[currentIndex].classList.remove('active');
        testimonialCards[currentIndex].style.opacity = '0';
        
        // Mettre à jour l'index
        currentIndex = index;
        
        // Afficher la nouvelle carte
        testimonialCards[currentIndex].classList.add('active');
        testimonialCards[currentIndex].style.opacity = '1';
        
        // Mettre à jour les indicateurs
        updateDots();
        
        // Réactiver les interactions après l'animation
        setTimeout(() => {
            isAnimating = false;
        }, 500);
    }

    // Fonction pour mettre à jour les indicateurs
    function updateDots() {
        dots.forEach((dot, index) => {
            dot.classList.toggle('active', index === currentIndex);
        });
    }

    // Fonction pour le témoignage suivant
    function nextTestimonial() {
        showTestimonial(currentIndex + 1);
    }

    // Fonction pour le témoignage précédent
    function prevTestimonial() {
        showTestimonial(currentIndex - 1);
    }

    // Démarrer le défilement automatique
    function startAutoSlide() {
        autoSlideInterval = setInterval(nextTestimonial, intervalDuration);
    }

    // Arrêter le défilement automatique
    function stopAutoSlide() {
        clearInterval(autoSlideInterval);
    }

    // Événements pour les boutons
    nextBtn.addEventListener('click', function() {
        stopAutoSlide();
        nextTestimonial();
        startAutoSlide();
    });

    prevBtn.addEventListener('click', function() {
        stopAutoSlide();
        prevTestimonial();
        startAutoSlide();
    });

    // Événements pour les indicateurs
    dots.forEach((dot, index) => {
        dot.addEventListener('click', function() {
            if (index !== currentIndex) {
                stopAutoSlide();
                showTestimonial(index);
                startAutoSlide();
            }
        });
    });

    // Pause au survol
    testimonialContainer.addEventListener('mouseenter', stopAutoSlide);
    testimonialContainer.addEventListener('mouseleave', startAutoSlide);

    // Gestion des événements tactiles
    let touchStartX = 0;
    let touchEndX = 0;

    testimonialContainer.addEventListener('touchstart', function(e) {
        touchStartX = e.changedTouches[0].clientX;
        stopAutoSlide();
    }, {passive: true});

    testimonialContainer.addEventListener('touchend', function(e) {
        touchEndX = e.changedTouches[0].clientX;
        handleSwipe();
        startAutoSlide();
    }, {passive: true});

    function handleSwipe() {
        const threshold = 50; // Seuil minimal de déplacement
        
        if (touchEndX < touchStartX - threshold) {
            nextTestimonial(); // Swipe gauche
        } else if (touchEndX > touchStartX + threshold) {
            prevTestimonial(); // Swipe droit
        }
    }

    // Initialisation
    function initCarousel() {
        // Masquer toutes les cartes sauf la première
        testimonialCards.forEach((card, index) => {
            if (index !== 0) {
                card.style.display = 'none';
            }
        });
        
        // Démarrer le défilement automatique
        startAutoSlide();
    }

    // Lancer le carrousel
    initCarousel();
});