import uuid
from datetime import datetime

import sqlalchemy.exc
from fastapi import HTTPException
from sqlalchemy import (Column, DateTime, ForeignKey, String, Text,
                        UniqueConstraint)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import backref, relationship
from starlette import status
from werkzeug.security import check_password_hash, generate_password_hash

from core.settings import settings
from db.psql import Base
from db.redis import RedisRepository, get_redis


class User(Base):
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    auth_history = relationship('AuthHistory', back_populates='user', cascade='all, delete', passive_deletes=True)

    def __init__(self, email: str, password: str) -> None:
        self.email = email
        self.password = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password, password)

    @classmethod
    async def get_user(cls, db: AsyncSession, email: str, password: str) -> 'User':
        """
        Асинхронно ищет пользователя по email
        :param db: AsyncSQLAlchemy сессия
        :param email: Email пользователя для поиска
        :param password: password для верификации
        :return: Объект пользователя или None, если не найден
        """
        async with db.begin():
            stmt = select(cls).where(cls.email == email)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()

            if user and user.check_password(password):
                return user

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Invalid credential'
            )

    @classmethod
    async def get_user_by_token(cls, db_session, token: str):
        from services.jwt import JWT
        async with db_session.begin():
            await JWT.check_logout(token)
            user_id = JWT.get_user_id(token)

            stmt = select(cls).where(cls.id == user_id)
            result = await db_session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail='Invalid token'
                )
            return user

    async def save(self, db: AsyncSession) -> dict:
        """
        Асинхронно сохраняет запись в базу данных
        :param db: AsyncSQLAlchemy сессия
        """
        async with db.begin():
            try:
                db.add(self)
                await db.flush()
                await db.refresh(self)
            except sqlalchemy.exc.IntegrityError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail='Credential already used'
                )

            return {'success': True}

    async def logout(self, token):
        """
        Асинхронно разлогинивает пользователя
        :param token: jwt-token
        """
        redis: RedisRepository = await get_redis()

        await redis.put_obj(f'{settings.prefix_logout_token}:{token}', '', settings.expiry_access)
        await redis.delete_obj(f'{settings.prefix_redis_token}:{str(self.id)}')

    def __repr__(self) -> str:
        return f'<User {self.email}>'


class SocialAccount(Base):
    __tablename__ = 'social_account'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)

    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    user = relationship(User, backref=backref('social_accounts', lazy=True))

    social_id = Column(Text, nullable=False)
    social_name = Column(Text, nullable=False)

    __table_args__ = (UniqueConstraint('social_id', 'social_name', name='social_pk'), )

    def __repr__(self):
        return f'<SocialAccount {self.social_name}:{self.user_id}>'