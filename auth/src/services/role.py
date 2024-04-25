import logging
from functools import lru_cache
from typing import Optional
from uuid import UUID

from fastapi import Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.psql import get_session
from models.roles import Role
from schemas.roles import RoleBase, RoleResponse

logger = logging.getLogger(__name__)


class RoleService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_roles(self) -> list[RoleResponse]:
        result = await self.db.execute(select(Role))
        return result.scalars().all()

    async def get_role_by_name(self, name: str) -> Optional[RoleResponse]:
        result = await self.db.execute(select(Role).where(Role.name == name))
        return result.scalars().first()

    async def create_role(self, role_create: RoleBase) -> RoleResponse:
        role = Role(**jsonable_encoder(role_create))
        self.db.add(role)
        await self.db.commit()
        await self.db.refresh(role)
        return role

    async def patch_role(
        self, role_id: UUID, role_patch: RoleBase
    ) -> Optional[RoleResponse]:
        values = jsonable_encoder(role_patch)
        result = await self.db.execute(
            update(Role).where(Role.id == role_id)
            .values(**values).returning(Role)
        )
        await self.db.commit()
        return result.scalars().first()

    async def delete_role(self, role_id: UUID) -> bool:
        result = await self.db.execute(delete(Role).where(Role.id == role_id))
        await self.db.commit()
        return result.rowcount


@lru_cache()
def get_role_service(
    db: AsyncSession = Depends(get_session),
) -> RoleService:
    return RoleService(db)
