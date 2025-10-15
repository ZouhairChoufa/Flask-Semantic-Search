document.addEventListener('DOMContentLoaded', function() {
    const indexBtn = document.getElementById('btn-indexer');
    const indexLogo = document.getElementById('logo-indexer');
    const loaderOverlay = document.getElementById('loader-overlay');

    const showLoader = (event) => {
        if (loaderOverlay) {
            event.preventDefault(); 
            loaderOverlay.classList.add('visible');
            setTimeout(() => {
                window.location.href = event.currentTarget.href;
            }, 100);
        }
    };

    if (indexBtn) {
        indexBtn.addEventListener('click', showLoader);
    }
    
    if (indexLogo) {
        indexLogo.addEventListener('click', showLoader);
    }
});

document.addEventListener('DOMContentLoaded', function() {
    const indexerButton = document.getElementById('btn-indexer');
    const loaderOverlay = document.getElementById('loader-overlay');

    if (indexerButton) {
        indexerButton.addEventListener('click', function(event) {
            event.preventDefault();
            if (loaderOverlay) {
                loaderOverlay.style.display = 'flex';
            }
            fetch(this.href)
                .then(response => {
                    window.location.reload();
                })
                .catch(error => {
                    console.error("Erreur lors du lancement de l'indexation:", error);
                    if (loaderOverlay) {
                        loaderOverlay.style.display = 'none';
                    }
                    alert("Une erreur est survenue. Veuillez consulter la console.");
                });
        });
    }
});