import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration de l'application."""
    SECRET_KEY = os.getenv("SECRET_KEY", "une-cle-secrete-tres-difficile-a-deviner")
    
    ES_HOST = os.getenv("ES_HOST", "http://localhost:9200")
    ES_INDEX = os.getenv("ES_INDEX", "wikidata_advanced_index")
    
    WIKIDATA_SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
    
    SCIENTIST_LIMIT = 3000
    MOVIE_LIMIT = 4000
    COUNTRY_LIMIT = 300 