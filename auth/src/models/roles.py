import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import relationship

from db.psql import Base


class Role(Base):
    __tablename__ = 'roles'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    name = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    @classmethod
    async def get_permissions(cls, db: AsyncSession, user_id: uuid.uuid4):
        async with db.begin():
            subquery = select(UserRole.role_id).filter(UserRole.user_id == user_id)
            query = select(Role.name).filter(Role.id.in_(subquery))
            result = await db.execute(query)
            roles = result.scalars().all()
            if roles:
                return roles
        return None

    def __repr__(self) -> str:
        return f'<Role {self.name}>'


class UserRole(Base):
    __tablename__ = 'user_roles'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)

    user_id = Column(UUID(as_uuid=True),
                     ForeignKey('users.id', ondelete='CASCADE'),
                     nullable=False)
    role_id = Column(UUID(as_uuid=True),
                     ForeignKey('roles.id', ondelete='CASCADE'),
                     nullable=False)
    role = relationship('Role')

    def __repr__(self) -> str:
        return f'<UserRole {self.role_id}>'
