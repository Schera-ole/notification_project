from abc import ABC, abstractmethod


class AsyncCacheStorage(ABC):
    @abstractmethod
    async def get_obj(self, *args, **kwargs):
        pass

    @abstractmethod
    async def put_obj(self, *args, **kwargs):
        pass

    @abstractmethod
    async def delete_obj(self, *args, **kwargs):
        pass
