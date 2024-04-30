import json
import uuid
from datetime import datetime, timedelta

import jwt
from fastapi import HTTPException, status

from core.settings import settings
from db.redis import RedisRepository, get_redis

from .oauth import YandexProvider


class JWTException:
    def invalid_token(self):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid credentials',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    def expiry_token(self):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Expiry credentials',
            headers={'WWW-Authenticate': 'Bearer'},
        )


class JWT:
    @classmethod
    def create_token(cls, body: dict):
        return jwt.encode(body, settings.secret_key, algorithm=settings.jwt_algorithm)

    @classmethod
    async def check_logout(cls, token: str):
        redis: RedisRepository = await get_redis()
        obj = await redis.get_obj(f'{settings.prefix_logout_token}:{token}')

        if obj is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Expiry credentials'
            )

    @classmethod
    def verify(cls, token: str) -> dict:
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
            expiry_at = payload['exp']

            if int(datetime.utcnow().timestamp() * 1000) > expiry_at:
                return JWTException().expiry_token()

            return payload
        except jwt.DecodeError:
            return JWTException().invalid_token()

    @classmethod
    def get_user_id(cls, access_token: str) -> str:
        payload = cls.verify(access_token)
        return payload['user_id']

    @classmethod
    async def get_tokens(
            cls,
            user_id: uuid.uuid4,
            roles: list
    ) -> dict:
        """
        Функция возвращает access и refresh токены

        :param user_id: ID юзера в БД
        :return: dict
        """
        redis: RedisRepository = await get_redis()

        if data := await redis.get_obj(f'{settings.prefix_redis_token}:{str(user_id)}'):
            return json.loads(data)

        payload_access = {
            'user_id': str(user_id),
            'sub': 'praktikum',
            'exp': int((datetime.utcnow() + timedelta(seconds=settings.expiry_access)).timestamp() * 1000),
            'roles': roles
        }

        payload_refresh = {
            'user_id': str(user_id),
            'sub': 'praktikum',
            'exp': int((datetime.utcnow() + timedelta(seconds=settings.expiry_refresh)).timestamp() * 1000),
            'roles': roles
        }

        access = cls.create_token(payload_access)
        refresh = cls.create_token(payload_refresh)

        response = {
            'access': access,
            'refresh': refresh,
        }

        await redis.put_obj(
            key=f'{settings.prefix_redis_token}:{str(user_id)}',
            obj=response,
            cache_expired=settings.expiry_access  # ставим истечение по access ключу
        )

        return response

    async def login_by_yandex(
            self,
            code: int,
            yandex_provider: YandexProvider,

    ):
        result = await yandex_provider.register(code)
        if result is None:
            return status.BAD_REQUEST

        user_id, email = result[0], result[1]
        tokens = await self.get_tokens(
            user_id=user_id,
            roles=[],
        )
        if tokens is None:
            return status.BAD_REQUEST
        return tokens
