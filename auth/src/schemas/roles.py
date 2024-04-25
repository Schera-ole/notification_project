from uuid import UUID

from pydantic import BaseModel, Field

from schemas.base import OrjsonBaseModel


class RoleBase(OrjsonBaseModel):
    name: str = Field(title='Название')


class RoleResponse(RoleBase):
    id: UUID

    class Config:
        orm_mode = True


class UserRolesResponse(BaseModel):
    user_id: UUID
    roles: list


class UserRoleInput(BaseModel):
    user_id: UUID
    role_id: UUID
