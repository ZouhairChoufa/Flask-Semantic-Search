import requests
from config import Config

def run_sparql_query(query):
    """Exécute une requête SPARQL et retourne les résultats."""
    headers = {
        'Accept': 'application/sparql-results+json',
        'User-Agent': 'AdvancedSemanticSearch/1.0 (Python/Requests)'
    }
    try:
        response = requests.get(
            Config.WIKIDATA_SPARQL_ENDPOINT,
            params={'query': query},
            headers=headers,
            timeout=240  
        )
        response.raise_for_status()
        return response.json()['results']['bindings']
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la requête SPARQL : {e}")
        return []

def fetch_scientist_data():
    """Récupère les données sur les chercheurs depuis Wikidata."""
    print(f"Récupération de {Config.SCIENTIST_LIMIT} chercheurs...")
    query = f"""
    SELECT ?item ?itemLabel ?itemDescription ?dateNaissance ?lieuNaissanceLabel ?domaineLabel ?image ?nationalityLabel
    WHERE {{
        VALUES ?occupation {{ wd:Q1650915 wd:Q901 }}  # Scientifique ou chercheur
        ?item wdt:P106 ?occupation.
        
        OPTIONAL {{ ?item wdt:P27 ?nationality. }}
        OPTIONAL {{ ?item wdt:P569 ?dateNaissance. }}
        OPTIONAL {{ ?item wdt:P19 ?lieuNaissance. }}
        OPTIONAL {{ ?item wdt:P101 ?domaine. }}
        OPTIONAL {{ ?item wdt:P18 ?image. }}
        
        SERVICE wikibase:label {{ bd:serviceParam wikibase:language "fr,en,de,es". }}
    }}
    LIMIT {Config.SCIENTIST_LIMIT}
    """
    return run_sparql_query(query)

def fetch_movie_data():
    """Récupère les données sur les films depuis Wikidata."""
    print(f"Récupération de {Config.MOVIE_LIMIT} films...")
    query = f"""
    SELECT ?item ?itemLabel ?itemDescription ?realisateurLabel ?dateDeSortie ?genreLabel ?image
    WHERE {{
        ?item wdt:P31 wd:Q11424.  # Instance de film
        
        OPTIONAL {{ ?item wdt:P57 ?realisateur. }}
        OPTIONAL {{ ?item wdt:P577 ?dateDeSortie. }}
        OPTIONAL {{ ?item wdt:P136 ?genre. }}
        OPTIONAL {{ ?item wdt:P18 ?image. }}
        
        SERVICE wikibase:label {{ bd:serviceParam wikibase:language "fr,en,de,es". }}
    }}
    LIMIT {Config.MOVIE_LIMIT}
    """
    return run_sparql_query(query)

def fetch_country_data():
    """Récupère les données sur les pays depuis Wikidata."""
    print(f"Récupération de {Config.COUNTRY_LIMIT} pays...")
    query = f"""
    SELECT ?item ?itemLabel ?itemDescription ?capitaleLabel ?continentLabel ?image
    WHERE {{
        ?item wdt:P31 wd:Q6256.  # Instance de pays
        
        OPTIONAL {{ ?item wdt:P36 ?capitale. }}
        OPTIONAL {{ ?item wdt:P30 ?continent. }}
        OPTIONAL {{ ?item wdt:P18 ?image. }}
        
        SERVICE wikibase:label {{ bd:serviceParam wikibase:language "fr,en,de,es". }}
    }}
    LIMIT {Config.COUNTRY_LIMIT}
    """
    return run_sparql_query(query)