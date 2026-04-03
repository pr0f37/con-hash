from dataclasses import dataclass, field
from typing import Self


from con_hash.connector import RedisConnector


class FakeRedis:
    def __init__(self, url: str, socket_timeout: float | None = None):
        self.url = url
        self.socket_timeout = socket_timeout

    @classmethod
    def from_url(cls, url: str, socket_timeout: float | None = None) -> Self:
        return cls(url, socket_timeout)

    def ping(self):
        return True


@dataclass()
class FakeConfig:
    REDIS_DSNS: list = field(default_factory=lambda: [1, 2, 3, 4, 5])
    REDIS_CONN_MULTIPLIER: int = 2
    FILENAME: str = "fake_path"


def test_redis_connector():
    config = FakeConfig()
    connector = RedisConnector(config, FakeRedis)
    len(connector.clients) == 5
    assert connector.clients[0] is connector.active_connections[0]
    assert connector.clients[0] is connector.active_connections[5]


def test_redis_remove_connections():
    config = FakeConfig()
    connector = RedisConnector(config, FakeRedis)
    len(connector.clients) == 5
    for client in connector.clients:
        connector.remove_active_connection(client)
    assert all(conn is None for conn in connector.active_connections)


def test_redis_get_connection():
    config = FakeConfig()
    connector = RedisConnector(config, FakeRedis)
    con = connector.get_active_connection(0)
    assert con is connector.clients[0]
    con_5 = connector.get_active_connection(5)
    assert con_5 is connector.clients[0]


def test_redis_one_conn_unavail():
    config = FakeConfig()
    connector = RedisConnector(config, FakeRedis)
    # monkey patch the ping() method to return False for client 0
    connector.clients[0].ping = lambda: False
    # the connections that use that client are returning ping False cause
    # they're patched,
    assert connector.active_connections[0].ping() is False
    assert connector.active_connections[5].ping() is False
    # active connection 1 is not patched and returns True
    assert connector.active_connections[1].ping() is True

    assert connector.active_connections[0] is not None
    assert connector.active_connections[5] is not None
    # after calling get_active_connection on connection number 0
    # connector will check if this connection is active (which will fail)
    con = connector.get_active_connection(0)
    # after failed check this connection will be removed from active_connections
    assert connector.active_connections[0] is None
    assert connector.active_connections[5] is None
    # but the client still remains in case this will become active in the future
    assert connector.clients[0] is not None
    # since connection number 0 is not active anymore
    # connector gives back next connection that's available
    assert con is connector.clients[1]
    assert connector.get_active_connection(5) is connector.clients[1]
    # other connections are not affected
    assert connector.get_active_connection(1) is connector.clients[1]
