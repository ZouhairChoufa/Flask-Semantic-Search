import re
import json
from elasticsearch import Elasticsearch, exceptions
from elasticsearch.helpers import bulk
from config import Config

es_client = None
def get_es_client():
    """Crée et retourne un client Elasticsearch singleton."""
    global es_client
    if es_client is None:
        try:
            es_client = Elasticsearch(
                hosts=[Config.ES_HOST],
                request_timeout=30,
                max_retries=3,
                retry_on_timeout=True
            )
            if not es_client.ping():
                raise exceptions.ConnectionError("Ping vers Elasticsearch a échoué.")
            print("Connexion à Elasticsearch réussie.")
        except exceptions.ConnectionError as e:
            print(f"ERREUR de connexion à Elasticsearch: {e}")
            es_client = None
    return es_client

def index_data_in_elasticsearch(all_data):
    """Indexe les données en utilisant l'API bulk pour des performances optimales."""
    es = get_es_client()
    if es is None:
        return 0, "Client Elasticsearch non disponible."

    index_settings = {
        "settings": {
            "analysis": {
                "analyzer": {
                    "french_custom": {
                        "type": "custom", "tokenizer": "standard",
                        "filter": ["lowercase", "asciifolding", "french_elision", "french_stop", "french_stemmer"]
                    }
                },
                "filter": {
                    "french_elision": {"type": "elision", "articles_case": True, "articles": ["l", "m", "t", "qu", "n", "s", "j", "d", "c", "jusqu", "quoiqu", "lorsqu", "puisqu"]},
                    "french_stop": {"type": "stop", "stopwords": "_french_"},
                    "french_stemmer": {"type": "stemmer", "language": "light_french"}
                }
            }
        },
        "mappings": {
            "properties": {
                "name": {"type": "text", "analyzer": "french_custom", "fields": {"keyword": {"type": "keyword"}}},
                "description": {"type": "text", "analyzer": "french_custom"},
                "type": {"type": "keyword"},
                "details": {
                    "properties": {
                        "birth_date": {"type": "date"}, "release_date": {"type": "date"},
                        "director": {"type": "text", "analyzer": "french_custom"},
                        "genre": {"type": "text", "analyzer": "french_custom"},
                        "nationality": {"type": "text", "analyzer": "french_custom"},
                        "domain": {"type": "text", "analyzer": "french_custom"},
                    }
                }
            }
        }
    }
    try:
        if es.indices.exists(index=Config.ES_INDEX):
            es.indices.delete(index=Config.ES_INDEX)
        es.indices.create(index=Config.ES_INDEX, body=index_settings)

        actions = [{"_op_type": "index", "_index": Config.ES_INDEX, "_id": item['uri'], "_source": item}
                for item in all_data if item.get('name') and item.get('uri')]
        
        success, errors = bulk(es, actions, raise_on_error=False)
        if errors: print(f"ERREURS pendant l'indexation: {errors}")

        es.indices.refresh(index=Config.ES_INDEX)
        message = f"Indexation terminée. {success} documents ajoutés."
        return success, message
    except Exception as e:
        error_message = f"Erreur lors de l'indexation: {e}"
        return 0, error_message

class QueryParser:
    """Analyse une chaîne de requête pour en extraire des filtres structurés."""
    def __init__(self, query_text):
        self.raw_query = query_text
        self.query_to_parse = f" {query_text.lower()} "
        self.must_clauses = []
        self.filter_clauses = []
        self.detected_type = None
        self.extractors = [
            self._extract_entity_type, self._extract_year, self._extract_director,
            self._extract_generic_attribute, self._extract_nationality
        ]

    def parse(self):
        """Lance tous les extracteurs et retourne les clauses."""
        for extractor in self.extractors:
            extractor()
        return self.must_clauses, self.filter_clauses

    def _remove_match_from_query(self, text_to_remove):
        self.query_to_parse = self.query_to_parse.replace(text_to_remove.lower(), " ")

    def _extract_entity_type(self):
        type_keywords = {
            'film': ['film', 'films'],
            'chercheur': ['chercheur', 'chercheurs', 'scientifique', 'scientifiques'],
            'pays': ['pays']
        }
        for type_name, keywords in type_keywords.items():
            for keyword in keywords:
                if f" {keyword} " in self.query_to_parse:
                    self.detected_type = type_name
                    self.filter_clauses.append({"term": {"type": self.detected_type}})
                    self._remove_match_from_query(keyword)
                    return

    def _extract_year(self):
        match = re.search(r'\b(avant|après|en|depuis|dans les années)\s*(\d{4})\b', self.query_to_parse, re.IGNORECASE)
        if match:
            qualifier, year_str = match.groups()
            year = int(year_str)
            range_query = {}
            if qualifier == 'avant': range_query['lte'] = f"{year}-12-31"
            elif qualifier in ['après', 'depuis']: range_query['gte'] = f"{year}-01-01"
            elif "années" in qualifier:
                range_query['gte'] = f"{year}-01-01"
                range_query['lte'] = f"{year+9}-12-31"
            else:
                range_query['gte'] = f"{year}-01-01"
                range_query['lte'] = f"{year}-12-31"
            
            date_fields = []
            if self.detected_type != 'film': date_fields.append("details.birth_date")
            if self.detected_type != 'chercheur': date_fields.append("details.release_date")
            
            if date_fields:
                self.filter_clauses.append({"bool": {"should": [{"range": {field: range_query}} for field in date_fields], "minimum_should_match": 1}})
            self._remove_match_from_query(match.group(0))

    def _extract_director(self):
        match = re.search(r'(?:film de|réalisé par|par)\s+([\w\s-]+)', self.query_to_parse, re.IGNORECASE)
        if match:
            director_name = match.group(1).strip()
            self.must_clauses.append({"match_phrase": {"details.director": director_name}})
            if not self.detected_type: self.filter_clauses.append({"term": {"type": "film"}})
            self._remove_match_from_query(match.group(0))
            self._remove_match_from_query(director_name)

    def _extract_generic_attribute(self):
        attributes = {
            'genre': ('genre', 'film'),
            'domaine': ('domain', 'chercheur')
        }
        for keyword, (field, entity_type) in attributes.items():
            match = re.search(fr'{keyword}\s+([\w\-]+)', self.query_to_parse, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                self.must_clauses.append({"match": {f"details.{field}": value}})
                if not self.detected_type: self.filter_clauses.append({"term": {"type": entity_type}})
                self._remove_match_from_query(match.group(0))
    
    def _extract_nationality(self):
        nationality_map = {"français": "France", "française": "France", "americain": "États-Unis", "americaine": "États-Unis", "britannique": "Royaume-Uni"}
        for adj, country in nationality_map.items():
            if f" {adj} " in self.query_to_parse:
                self.must_clauses.append({"match": {"details.nationality": country}})
                if not self.detected_type: self.filter_clauses.append({"term": {"type": "chercheur"}})
                self._remove_match_from_query(adj)
                return

def search_in_elasticsearch(query_text, from_offset=0, size=10):
    """
    Effectue une recherche flexible en combinant des filtres stricts (extraits de la requête)
    avec une recherche textuelle globale sur la requête originale.
    """
    es = get_es_client()
    if not es or not query_text:
        return None

    if not es.indices.exists(index=Config.ES_INDEX):
        return None

    parser = QueryParser(query_text)
    must_clauses, filter_clauses = parser.parse()

    should_clauses = [
        {
            "multi_match": {
                "query": query_text,  
                "fields": [
                    "name^4",          
                    "description^2",  
                    "details.director",
                    "details.genre",
                    "details.domain",
                    "details.nationality"
                ],
                "type": "best_fields",
                "fuzziness": "AUTO"
            }
        },
        {
            "multi_match": { 
                "query": query_text,
                "fields": ["name"],
                "type": "phrase",
                "boost": 5
            }
        }
    ]

    search_query = {
        "query": {
            "bool": {
                "must": must_clauses,      
                "filter": filter_clauses,  
                "should": should_clauses,    
                "minimum_should_match": 1 if not must_clauses else 0
            }
        }
    }
    
    try:
        print(json.dumps(search_query, indent=2, ensure_ascii=False))
        response = es.search(index=Config.ES_INDEX, body=search_query, from_=from_offset, size=size)
        return {'hits': response['hits']['hits'], 'total': response['hits']['total']['value']}
    except Exception as e:
        print(f"Erreur lors de la recherche : {e}")
        return None