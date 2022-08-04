import json
import logging
import os
import sys

import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(
    __file__))))
sys.path.append(BASE_DIR)
from example import settings  # noqa: E402

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

with open(f'{settings.ES_SCHEMAS_DIR}movies.json', 'r') as schema:
    movies_schema = json.loads(schema.read())

r = requests.put(f'{settings.ES_BASE_URL}/movies', json=movies_schema)

logger.info(r.json())
