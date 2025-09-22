// Gestion des notifications
document.addEventListener('DOMContentLoaded', function() {
    // Toggle des notifications
    const notificationsBtn = document.getElementById('notifications-btn');
    const notificationsDropdown = document.getElementById('notifications-dropdown');
    
    if (notificationsBtn && notificationsDropdown) {
        notificationsBtn.addEventListener('click', function() {
            notificationsDropdown.classList.toggle('hidden');
            loadNotifications();
        });
        
        // Fermer les notifications en cliquant ailleurs
        document.addEventListener('click', function(event) {
            if (!notificationsBtn.contains(event.target) && !notificationsDropdown.contains(event.target)) {
                notificationsDropdown.classList.add('hidden');
            }
        });
    }
    
    // Charger les notifications au chargement de la page
    loadNotifications();
    
    // Actualiser les notifications toutes les 30 secondes
    setInterval(loadNotifications, 30000);
});

// Charger les notifications depuis l'API
function loadNotifications() {
    fetch('/api/notifications')
        .then(response => {
            if (response.redirected) {
                // L'utilisateur n'est pas connecté, ne pas afficher d'erreur
                return null;
            }
            return response.json();
        })
        .then(data => {
            if (data) {
                updateNotificationCount(data.notifications.length);
                displayNotifications(data.notifications);
            }
        })
        .catch(error => {
            // Ne pas afficher d'erreur si l'utilisateur n'est pas connecté
            if (!error.message.includes('Unexpected token')) {
                console.error('Erreur lors du chargement des notifications:', error);
            }
        });
}

// Mettre à jour le compteur de notifications
function updateNotificationCount(count) {
    const notificationCount = document.getElementById('notification-count');
    if (notificationCount) {
        if (count > 0) {
            notificationCount.textContent = count;
            notificationCount.classList.remove('hidden');
        } else {
            notificationCount.classList.add('hidden');
        }
    }
}

// Afficher les notifications dans le dropdown
function displayNotifications(notifications) {
    const notificationsList = document.getElementById('notifications-list');
    if (!notificationsList) return;
    
    if (notifications.length === 0) {
        notificationsList.innerHTML = `
            <div class="px-4 py-3 text-sm text-gray-500 text-center">
                Aucune nouvelle notification
            </div>
        `;
        return;
    }
    
    notificationsList.innerHTML = '';
    notifications.forEach(notification => {
        const notificationItem = document.createElement('div');
        notificationItem.className = 'px-4 py-3 hover:bg-gray-50 border-b border-gray-100 last:border-b-0';
        
        const icon = getNotificationIcon(notification.type);
        const timeAgo = formatTimeAgo(notification.created_at);
        
        notificationItem.innerHTML = `
            <div class="flex items-start space-x-3">
                <div class="flex-shrink-0 text-${getNotificationColor(notification.type)}">
                    ${icon}
                </div>
                <div class="flex-1 min-w-0">
                    <p class="text-sm text-gray-900">${notification.message}</p>
                    <p class="text-xs text-gray-500 mt-1">${timeAgo}</p>
                </div>
                <button onclick="markNotificationAsRead(${notification.id})" 
                        class="text-gray-400 hover:text-gray-600">
                    <i class="fas fa-times text-xs"></i>
                </button>
            </div>
        `;
        
        notificationsList.appendChild(notificationItem);
    });
}

// Obtenir l'icône appropriée pour le type de notification
function getNotificationIcon(type) {
    switch (type) {
        case 'message':
            return '<i class="fas fa-envelope"></i>';
        case 'like':
            return '<i class="fas fa-heart"></i>';
        case 'match':
            return '<i class="fas fa-users"></i>';
        default:
            return '<i class="fas fa-bell"></i>';
    }
}

// Obtenir la couleur appropriée pour le type de notification
function getNotificationColor(type) {
    switch (type) {
        case 'message':
            return 'blue-500';
        case 'like':
            return 'red-500';
        case 'match':
            return 'green-500';
        default:
            return 'gray-500';
    }
}

// Marquer une notification comme lue
function markNotificationAsRead(notificationId) {
    fetch(`/api/notifications/${notificationId}/read`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadNotifications(); // Recharger les notifications
        }
    })
    .catch(error => {
        console.error('Erreur lors de la marque comme lue:', error);
    });
}

// Formater le temps écoulé
function formatTimeAgo(timestamp) {
    const now = new Date();
    const date = new Date(timestamp);
    const diffInSeconds = Math.floor((now - date) / 1000);
    
    if (diffInSeconds < 60) {
        return 'À l\'instant';
    } else if (diffInSeconds < 3600) {
        const minutes = Math.floor(diffInSeconds / 60);
        return `Il y a ${minutes} minute${minutes > 1 ? 's' : ''}`;
    } else if (diffInSeconds < 86400) {
        const hours = Math.floor(diffInSeconds / 3600);
        return `Il y a ${hours} heure${hours > 1 ? 's' : ''}`;
    } else {
        const days = Math.floor(diffInSeconds / 86400);
        return `Il y a ${days} jour${days > 1 ? 's' : ''}`;
    }
}

// Gestion des messages flash
function showFlashMessage(message, type = 'success') {
    const flashContainer = document.createElement('div');
    flashContainer.className = `fixed top-4 right-4 z-50 bg-${type === 'success' ? 'green' : 'red'}-100 border border-${type === 'success' ? 'green' : 'red'}-400 text-${type === 'success' ? 'green' : 'red'}-700 px-4 py-3 rounded shadow-lg`;
    
    flashContainer.innerHTML = `
        <div class="flex items-center space-x-2">
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" class="text-${type === 'success' ? 'green' : 'red'}-500 hover:text-${type === 'success' ? 'green' : 'red'}-700">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    document.body.appendChild(flashContainer);
    
    // Auto-supprimer après 5 secondes
    setTimeout(() => {
        if (flashContainer.parentElement) {
            flashContainer.remove();
        }
    }, 5000);
}

// Fonction utilitaire pour les requêtes AJAX
function apiRequest(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'same-origin'
    };
    
    return fetch(url, { ...defaultOptions, ...options })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        });
}

// Gestion des erreurs globales
window.addEventListener('error', function(event) {
    console.error('Erreur JavaScript:', event.error);
    showFlashMessage('Une erreur est survenue. Veuillez réessayer.', 'error');
});

// Gestion des erreurs de requêtes fetch
window.addEventListener('unhandledrejection', function(event) {
    console.error('Erreur de requête:', event.reason);
    showFlashMessage('Erreur de connexion. Vérifiez votre connexion internet.', 'error');
});

// Fonction pour confirmer les actions importantes
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Fonction pour formater les dates
function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffInDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));
    
    if (diffInDays === 0) {
        return 'Aujourd\'hui';
    } else if (diffInDays === 1) {
        return 'Hier';
    } else if (diffInDays < 7) {
        return `Il y a ${diffInDays} jours`;
    } else {
        return date.toLocaleDateString('fr-FR');
    }
}

// Fonction pour valider les formulaires
function validateForm(formElement) {
    const inputs = formElement.querySelectorAll('input[required], select[required], textarea[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('border-red-500');
            isValid = false;
        } else {
            input.classList.remove('border-red-500');
        }
    });
    
    return isValid;
}

// Initialisation des tooltips et autres composants UI
document.addEventListener('DOMContentLoaded', function() {
    // Initialiser les tooltips si nécessaire
    if (typeof tippy !== 'undefined') {
        tippy('[data-tippy-content]');
    }
    
    // Initialiser les composants de date si nécessaire
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(input => {
        if (!input.value) {
            const today = new Date().toISOString().split('T')[0];
            input.setAttribute('max', today);
        }
    });
});
