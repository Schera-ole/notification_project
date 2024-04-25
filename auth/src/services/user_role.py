import logging
from functools import lru_cache
from uuid import UUID

from fastapi import Depends
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.psql import get_session
from models.roles import Role, UserRole
from models.user import User

logger = logging.getLogger(__name__)


class UserRoleService:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.auth_service = User

    async def get_user_by_id(self, user_id: UUID) -> User:
        result = await self.db_session.execute(select(User).where(User.id == user_id))
        return result.scalars().first()

    async def get_role_by_id(self, role_id: UUID) -> Role:
        result = await self.db_session.execute(select(Role).where(Role.id == role_id))
        return result.scalars().first()

    async def get_user_role(
        self, user_id: UUID, role_id: UUID
    ) -> UserRole:
        result = await self.db_session.execute(
            select(UserRole).where(UserRole.user_id == user_id,
                                   UserRole.role_id == role_id)
        )
        return result.scalars().first()

    async def get_user_roles(
        self, user_id: UUID
    ) -> dict:
        roles = await Role.get_permissions(self.db_session, user_id)
        response = {}
        if roles:
            response['user_id'] = user_id
            response['roles'] = roles
        return response

    async def create_user_role(
        self, user_id: UUID, role_id: UUID
    ) -> None:
        user_role = UserRole(user_id=user_id, role_id=role_id)
        self.db_session.add(user_role)
        await self.db_session.commit()

    async def delete_user_role(
        self, user_id: UUID, role_id: UUID
    ) -> bool:
        result = await self.db_session.execute(
            delete(UserRole).where(UserRole.role_id == role_id,
                                   UserRole.user_id == user_id)
        )
        await self.db_session.commit()
        return result.rowcount


@lru_cache()
def get_user_role_service(
    db: AsyncSession = Depends(get_session),
) -> UserRoleService:
    return UserRoleService(db)
