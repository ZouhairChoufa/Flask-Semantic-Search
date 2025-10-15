# Moteur de Recherche Sémantique Avancé

Ce projet est une application web Flask fournissant un moteur de recherche sémantique qui interroge des données provenant de Wikidata et les indexe dans Elasticsearch.

## Fonctionnalités

-   **Interface de recherche** pour des requêtes en langage naturel.
-   **Analyse de la requête** pour extraire des entités (films, chercheurs) et des filtres (dates, nationalités).
-   **Indexation en un clic** des données depuis Wikidata vers Elasticsearch.
-   **Interface utilisateur réactive** avec retour visuel pendant l'indexation.

## Structure du Projet

-   `app.py`: Application Flask principale (routes).
-   `config.py`: Gestion de la configuration via des variables d'environnement.
-   `.env`: Fichier pour les variables d'environnement locales.
-   `requirements.txt`: Dépendances Python.
-   `/search`: Module Python pour la logique de recherche et d'indexation.
-   `/templates`: Modèles HTML (Jinja2).
-   `/static`: Fichiers CSS et JavaScript.

## Installation et Lancement

### Prérequis

-   Python 3.8+
-   Elasticsearch doit être installé et en cours d'exécution sur `http://localhost:9200`.
-   Un environnement virtuel Python est recommandé.

### Étapes

1.  **Clonez le projet et naviguez dans le répertoire :**
    ```bash
    git clone <votre-repo>
    cd semantic-search-project
    ```

2.  **Créez et activez un environnement virtuel :**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Sur Windows: venv\Scripts\activate
    ```

3.  **Installez les dépendances :**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Créez le fichier de configuration locale :**
    Copiez `.env.example` (s'il existe) ou créez un fichier `.env` et assurez-vous qu'il contient :
    ```
    ES_HOST=http://localhost:9200
    ES_INDEX=wikidata_advanced_index
    ```

5.  **Lancez l'application Flask :**
    ```bash
    flask run
    ```
    L'application sera disponible à l'adresse `http://127.0.0.1:5000`.

6.  **Lancez l'indexation :**
    Ouvrez votre navigateur, allez sur `http://127.0.0.1:5000` et cliquez sur le bouton "Lancer l'indexation".