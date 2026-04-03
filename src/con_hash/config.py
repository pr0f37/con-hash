from typing import Any
from pydantic_settings import BaseSettings
from pydantic import Field, RedisDsn, TypeAdapter
from dotenv import find_dotenv, load_dotenv
from pathlib import Path
from yaml import safe_load, YAMLError

load_dotenv(find_dotenv())


RedisDsnList = TypeAdapter(list[RedisDsn])


class Config(BaseSettings):
    REDIS_DSNS: list[RedisDsn] = Field(
        default_factory=lambda: [RedisDsn("redis://localhost:6379/0")]
    )
    REDIS_CONN_MULTIPLIER: int = Field(default=2, gt=0, lt=100)
    FILENAME: str = Field(default="static/redis_conns.yaml")

    def model_post_init(self, __context: Any):
        dir = Path.cwd()
        try:
            with open(dir.joinpath(self.FILENAME), "r") as r_file:
                dsns = safe_load(r_file)
        except YAMLError, FileNotFoundError, OSError:
            return
        self.REDIS_DSNS = RedisDsnList.validate_python(dsns)
