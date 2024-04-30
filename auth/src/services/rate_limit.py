import datetime

REQUEST_LIMIT_PER_MINUTE = 20
REDIS_EXPIRE_SECONDS = 60


class RateLimit:
    def __init__(self, host, redis):
        self.pipe_key = f'{host}:{datetime.datetime.now().minute}'
        self.pipe = redis.pipeline()

    async def rate_limit(self):
        self.pipe.incr(self.pipe_key, 1)
        self.pipe.expire(self.pipe_key, REDIS_EXPIRE_SECONDS)
        result = await self.pipe.execute()
        return not result[0] > REQUEST_LIMIT_PER_MINUTE
