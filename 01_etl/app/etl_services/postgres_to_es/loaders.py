import logging
import more_itertools
import psycopg2

from example import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PostgresLoader:
    def __init__(self, connection):
        self.connection = connection
        self.cursor = connection.cursor()
