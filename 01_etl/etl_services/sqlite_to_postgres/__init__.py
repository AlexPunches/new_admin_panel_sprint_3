import logging

from settings import BaseConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = BaseConfig()
