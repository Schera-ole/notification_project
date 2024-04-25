from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserInput(BaseModel):
    email: EmailStr
    password: str


class UserInDB(BaseModel):
    id: UUID
    email: EmailStr

    class Config:
        orm_mode = True
