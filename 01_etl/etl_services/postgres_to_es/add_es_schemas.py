import json

import requests

from postgres_to_es import logger, settings
from postgres_to_es.services import ElasticInsertError


def check_es_index(index_name: str) -> bool:
    r = requests.get(f'{settings.es_base_url}/_mapping').json()
    return bool(r.get(index_name))


def add_es_index(index_name: str, schema_path: str):
    with open(schema_path, 'r') as schema:
        es_schema = json.loads(schema.read())
    response = requests.put(
        f'{settings.es_base_url}/{index_name}', json=es_schema
    )
    if not response.ok:
        raise ElasticInsertError(response.json())
    logger.info('Добавлен Elasticsearch индекс "%s"', index_name)
