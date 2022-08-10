import logging

from settings import BaseConfig

settings = BaseConfig()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DbConnect:
    def __init__(self, connection):
        self.connection = connection
        self.cursor = connection.cursor()
