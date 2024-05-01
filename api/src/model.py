import uuid
from datetime import datetime
from uuid import UUID, uuid4
import sqlalchemy
from sqlalchemy import Column, DateTime, ForeignKey, String, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import relationship
from fastapi import HTTPException
from db.psql import Base
from starlette import status


class Template(Base):
    __tablename__ = 'templates'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    version = Column(Integer, nullable=True)
    name = Column(String, nullable=True, unique=True)
    text = Column(String(1024), nullable=True)

    def __init__(self, data) -> None:

        self.version = data.version
        self.name = data.name
        self.text = data.text


    @classmethod
    async def get_templates(cls, db: AsyncSession):
        async with db.begin():
            stmt = select(cls)
            result = await db.execute(stmt)
            templates = result.scalars().all()

            if templates:
                return templates

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Cant\'t find templates',
            )

    __table_args__ = ({"schema": "template"},)
    async def add_template(self, db: AsyncSession) -> dict:
        """
        Асинхронно сохраняет запись в базу данных
        :param db: AsyncSQLAlchemy сессия
        """
        print('qwdswqdasasd123')
        print(self.name)

        async with db.begin():
            try:

                db.add(self)
                await db.flush()
                await db.refresh(self)
            except sqlalchemy.exc.IntegrityError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail='Cant\'t add template',
                )

            return {'success': True}

    __table_args__ = ({"schema": "template"},)