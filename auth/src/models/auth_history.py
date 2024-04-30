import uuid
from datetime import datetime

import sqlalchemy.exc
from fastapi import HTTPException, status
from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import relationship, selectinload

from db.psql import Base


class AuthHistory(Base):
    __tablename__ = 'auth_history'
    __table_args__ = (
        UniqueConstraint('id', 'timestamp'),
        {
            'postgresql_partition_by': 'RANGE (timestamp)',
        }
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    user_agent = Column(String(255), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship('User', back_populates='auth_history')

    def __repr__(self) -> str:
        return f'<AuthHistory for User {self.user_id}>'

    async def save_auth_history(self, db: AsyncSession, user_agent) -> None:
        """
        Асинхронно сохраняет запись об авторизации в истории
        :param db: AsyncSQLAlchemy сессия
        """
        auth_history = AuthHistory(user_id=self.id, user_agent=user_agent)
        async with db.begin():
            db.add(auth_history)
            await db.flush()
            await db.refresh(auth_history)

    @classmethod
    async def get_auth_history(cls, db: AsyncSession, user_id, page_size, page_number):
        """
        Асинхронно получает историю авторизаций для пользователя
        :param db: AsyncSQLAlchemy сессия
        :param user_id: user id
        :param page_size: page size
        :param page_number: page number
        :return: List[AuthHistory]
        """
        async with db.begin():
            stmt = select(AuthHistory).filter(AuthHistory.user_id == user_id)
            stmt = stmt.offset(page_size * (page_number - 1)).limit(page_size)
            result = await db.execute(stmt.options(selectinload(AuthHistory.user)))
            return result.scalars().all()

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
                    detail='Something going wrong'
                )

            return {'success': True}
