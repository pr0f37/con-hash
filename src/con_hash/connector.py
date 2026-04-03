from redis import ConnectionError
from redis import Redis
from logging import getLogger
from con_hash.config import Config
from pydantic import RedisDsn


log = getLogger(__name__)


class NoRedisConnAvailableError(Exception):
    pass


class RedisConnector:
    def __init__(self, config: Config, conn_engine=Redis):
        self.conn_engine = conn_engine
        self.clients = self._build_redis_clients(config.REDIS_DSNS)
        self.active_connections = self._init_active_connections(
            config.REDIS_CONN_MULTIPLIER
        )

    def _build_redis_clients(self, dsns: list[RedisDsn]) -> list[Redis]:
        return [self.conn_engine.from_url(str(dsn), socket_timeout=5.0) for dsn in dsns]

    def _init_active_connections(self, multiplier: int) -> list[Redis | None]:
        return [client for client in self.clients] * multiplier

    def _get_connection(self, id: int) -> Redis:
        conn = None
        count = 0
        while conn is None and count < len(self.active_connections):
            conn = self.active_connections[(id + count) % len(self.active_connections)]
            count += 1
        if count == len(self.active_connections):
            raise NoRedisConnAvailableError
        return conn

    def remove_active_connection(self, removed_conn: Redis):
        for i in range(len(self.active_connections)):
            if self.active_connections[i] is removed_conn:
                self.active_connections[i] = None

    def get_active_connection(self, id: int) -> Redis:
        r = None
        while r is None:
            r = self._get_connection(id)
            try:
                if not r.ping():
                    raise ConnectionError
            except ConnectionError:
                log.warning(f"removing connection {r}")
                self.remove_active_connection(r)
                r = None
        return r
