from con_hash.config import Config
from con_hash.connector import RedisConnector

config = Config()

connector = RedisConnector(config)
