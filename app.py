import math
import re
import threading
from flask import Flask, jsonify, request, render_template, redirect, url_for, flash
from elasticsearch import exceptions
from config import Config
from search.es_utils import get_es_client, index_data_in_elasticsearch, search_in_elasticsearch
from search.wikidata_client import fetch_scientist_data, fetch_movie_data, fetch_country_data

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

INDEXING_STATUS = {
    'is_running': False,
    'message': 'Aucune indexation depuis le dernier démarrage.',
    'is_complete': False,
    'final_count': 0
}

def clean_date(date_str):
    """Nettoie une chaîne de date pour ne garder que AAAA-MM-JJ."""
    if not date_str:
        return None
    match = re.search(r"^\d{4}-\d{2}-\d{2}", date_str)
    return match.group(0) if match else None


def run_indexing_task():
    """Tâche d'indexation lourde qui gère les erreurs de source individuellement."""
    global INDEXING_STATUS
    INDEXING_STATUS = {
        'is_running': True, 'message': 'Initialisation...', 'is_complete': False, 'final_count': 0
    }
    
    all_data_to_index = []
    final_message = ""

    try:
        try:
            INDEXING_STATUS['message'] = "Étape 1/4 : Collecte des données sur les chercheurs..."
            for item in fetch_scientist_data():
                all_data_to_index.append({
                    'uri': item.get('item', {}).get('value'),
                    'name': item.get('itemLabel', {}).get('value'),
                    'description': item.get('itemDescription', {}).get('value'),
                    'type': 'chercheur', 'image': item.get('image', {}).get('value'),
                    'details': { 'birth_date': clean_date(item.get('dateNaissance', {}).get('value')), 'birth_place': item.get('lieuNaissanceLabel', {}).get('value'), 'domain': item.get('domaineLabel', {}).get('value'), 'nationality': item.get('nationalityLabel', {}).get('value') }
                })
        except Exception as e:
            print(f"AVERTISSEMENT: Échec de la collecte des chercheurs: {e}")
            INDEXING_STATUS['message'] = "Erreur lors de la collecte des chercheurs, passage à la suite..."

        try:
            INDEXING_STATUS['message'] = "Étape 2/4 : Collecte des données sur les films..."
            for item in fetch_movie_data():
                all_data_to_index.append({
                    'uri': item.get('item', {}).get('value'),
                    'name': item.get('itemLabel', {}).get('value'),
                    'description': item.get('itemDescription', {}).get('value'),
                    'type': 'film', 'image': item.get('image', {}).get('value'),
                    'details': { 'director': item.get('realisateurLabel', {}).get('value'), 'release_date': clean_date(item.get('dateDeSortie', {}).get('value')), 'genre': item.get('genreLabel', {}).get('value') }
                })
        except Exception as e:
            print(f"AVERTISSEMENT: Échec de la collecte des films: {e}")
            INDEXING_STATUS['message'] = "Erreur lors de la collecte des films, passage à la suite..."

        try:
            INDEXING_STATUS['message'] = "Étape 3/4 : Collecte des données sur les pays..."
            for item in fetch_country_data():
                all_data_to_index.append({
                    'uri': item.get('item', {}).get('value'),
                    'name': item.get('itemLabel', {}).get('value'),
                    'description': item.get('itemDescription', {}).get('value'),
                    'type': 'pays', 'image': item.get('image', {}).get('value'),
                    'details': { 'capital': item.get('capitaleLabel', {}).get('value'), 'continent': item.get('continentLabel', {}).get('value') }
                })
        except Exception as e:
            print(f"AVERTISSEMENT: Échec de la collecte des pays: {e}")
            INDEXING_STATUS['message'] = "Erreur lors de la collecte des pays, passage à la suite..."

        total_docs = len(all_data_to_index)
        if total_docs > 0:
            INDEXING_STATUS['message'] = f"Étape 4/4 : Indexation de {total_docs} documents..."
            count, es_message = index_data_in_elasticsearch(all_data_to_index)
            INDEXING_STATUS['final_count'] = count
            final_message = es_message
        else:
            final_message = "Aucun document n'a été collecté pour l'indexation."

    except Exception as e:
        final_message = f"Une erreur critique est survenue durant le processus : {e}"
    finally:
        INDEXING_STATUS['is_running'] = False
        INDEXING_STATUS['is_complete'] = True
        INDEXING_STATUS['message'] = final_message
        print(f"Thread d'indexation terminé. Message final : {final_message}")

@app.route('/', methods=['GET', 'POST'])
def search_interface():
    """Affiche l'interface de recherche principale."""
    query = request.form.get('query', request.args.get('query', '')).strip()
    page = int(request.args.get('page', 1))
    results, total_pages = None, 0

    es = get_es_client()
    if not es:
        flash("Connexion à Elasticsearch impossible. Vérifiez que le service est démarré.", 'error')
    
    if query and es:
        size = 10
        from_offset = (page - 1) * size
        results_data = search_in_elasticsearch(query, from_offset, size)
        
        if results_data is None:
            try:
                if not es.indices.exists(index=Config.ES_INDEX):
                    flash(f"L'index '{Config.ES_INDEX}' n'existe pas. Veuillez d'abord l'indexer.", 'warning')
            except exceptions.ConnectionError:
                flash("Connexion à Elasticsearch impossible.", 'error')
            results = {'hits': [], 'total': 0}
        else:
            results = results_data
            if results['total'] > 0:
                total_pages = math.ceil(results['total'] / size)

    return render_template('index.html', query=query, results=results, page=page, total_pages=total_pages)

@app.route('/index')
def indexing_status_page():
    """Affiche la page qui montre la progression de l'indexation."""
    return render_template('indexing_status.html')

@app.route('/start-indexing', methods=['POST'])
def start_indexing():
    """Déclenche l'indexation en arrière-plan."""
    if INDEXING_STATUS['is_running']:
        return jsonify({'status': 'already_running', 'message': 'Une indexation est déjà en cours.'})

    es = get_es_client()
    if not es:
        return jsonify({'status': 'error', 'message': 'Connexion à Elasticsearch impossible.'}), 500

    indexing_thread = threading.Thread(target=run_indexing_task)
    indexing_thread.start()
    return jsonify({'status': 'started', 'message': 'L\'indexation a été lancée.'})

@app.route('/check-status')
def check_status():
    """Retourne le statut actuel de l'indexation en JSON."""
    return jsonify(INDEXING_STATUS)

if __name__ == '__main__':
    app.run(debug=True, port=5000)