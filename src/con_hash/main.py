from logging import getLogger

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from redis import ConnectionError

from con_hash.bootstrap import connector
from con_hash.connector import NoRedisConnAvailableError

log = getLogger(__name__)

app = FastAPI(docs_url="/")


@app.exception_handler(NoRedisConnAvailableError)
async def redis_exception_handler(request: Request, exc: NoRedisConnAvailableError):
    raise HTTPException(
        status_code=500,
        detail="No active Redis connection available! Cannot store an item!",
    )


class Item(BaseModel):
    value: str
    id: int


class ItemsInRedis(BaseModel):
    db_name: str
    items: list[Item]


class Response(BaseModel):
    message: str


@app.post("/items/")
def save_item(item: Item) -> Response:
    r = connector.get_active_connection(item.id)
    if r.get(item.id):
        return Response(message=f"Item with this id: {item.id} already exits")
    else:
        r.set(name=item.id, value=item.value)
        return Response(message=f"Item {item} has been stored in Redis")


@app.get("/items/")
def get_all_items() -> list[ItemsInRedis]:
    items = []
    for client in connector.clients:
        try:
            if client.ping():
                items.append(
                    ItemsInRedis(
                        db_name=client.get_connection_kwargs()["host"],
                        items=[
                            Item(id=key, value=client.get(key))
                            for key in client.keys("*")
                        ],
                    )
                )
        except ConnectionError:
            continue
    return items
