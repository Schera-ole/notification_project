import json
import uuid

from redis.asyncio import Redis

from db.abc_classes import AsyncCacheStorage


class RedisRepository(AsyncCacheStorage):
    def __init__(self, redis_client: Redis) -> None:
        self.client = redis_client

    async def get_obj(self, key: uuid.uuid4):
        data = await self.client.get(key)
        if not data:
            return None
        return data

    async def put_obj(self, key: str, obj: dict, cache_expired):
        await self.client.set(key, json.dumps(obj), cache_expired)

    async def delete_obj(self, key: str):
        await self.client.delete(key)


redis: RedisRepository | None = None


async def get_redis() -> RedisRepository:
    return redis
