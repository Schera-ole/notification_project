'''
назначить пользователю роль;
отобрать у пользователя роль;
метод для проверки наличия прав у пользователя.'''
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Header, HTTPException, status
from fastapi.encoders import jsonable_encoder
from opentelemetry import trace
from sqlalchemy.ext.asyncio import AsyncSession

from db.psql import get_session
from schemas.base import HTTPExceptionResponse
from schemas.roles import UserRoleInput
from services.user_role import UserRoleService, get_user_role_service
from services.verify import is_admin, security_jwt

tracer = trace.get_tracer(__name__)
router = APIRouter()


@router.post(
    '/',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Добавление роли пользователю',

    responses={
        status.HTTP_400_BAD_REQUEST: {'model': HTTPExceptionResponse},
        status.HTTP_401_UNAUTHORIZED: {'model': HTTPExceptionResponse},
        status.HTTP_403_FORBIDDEN: {'model': HTTPExceptionResponse},
    }
)
async def create_user_role(
    input: UserRoleInput,
    decoded_token: dict = Depends(security_jwt),
    user_role_service: UserRoleService = Depends(get_user_role_service),
    db_session: AsyncSession = Depends(get_session),
    X_Request_Id: str = Header(...),
) -> None:
    is_admin(decoded_token['roles'])
    data = jsonable_encoder(input)
    with tracer.start_span('create_user_role') as span:
        span.set_attribute('request-id', X_Request_Id)

    if not await user_role_service.get_user_by_id(data['user_id']):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='User not found')
    if not await user_role_service.get_role_by_id(data['role_id']):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Role not found')
    if await user_role_service.get_user_role(data['user_id'], data['role_id']):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='User role already exists')
    await user_role_service.create_user_role(data['user_id'], data['role_id'])


@router.delete(
    '/',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Удаление роли у пользователя',
    responses={
        status.HTTP_401_UNAUTHORIZED: {'model': HTTPExceptionResponse},
        status.HTTP_403_FORBIDDEN: {'model': HTTPExceptionResponse},
        status.HTTP_404_NOT_FOUND: {'model': HTTPExceptionResponse},
    }
)
async def delete_user_role(
    input: UserRoleInput,
    decoded_token: dict = Depends(security_jwt),
    user_role_service: UserRoleService = Depends(get_user_role_service),
    authorization: str = Header(None),
    db_session: AsyncSession = Depends(get_session),
    X_Request_Id: str = Header(...),
) -> None:
    is_admin(decoded_token['roles'])
    data = jsonable_encoder(input)
    with tracer.start_span('delete_user_role') as span:
        span.set_attribute('request-id', X_Request_Id)

    if not await user_role_service.delete_user_role(data['user_id'], data['role_id']):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='User role not found')


@router.get(
    '/',
    summary='Проверка наличия прав у пользователя',
    responses={
        status.HTTP_401_UNAUTHORIZED: {'model': HTTPExceptionResponse},
        status.HTTP_403_FORBIDDEN: {'model': HTTPExceptionResponse},
        status.HTTP_404_NOT_FOUND: {'model': HTTPExceptionResponse},
    }
)
async def check_roles_user(
    decoded_token: dict = Depends(security_jwt),
    user_id: Optional[UUID] = Body(None, embed=True),
    user_role_service: UserRoleService = Depends(get_user_role_service),
    db_session: AsyncSession = Depends(get_session),
    X_Request_Id: str = Header(...),
) -> dict:
    with tracer.start_span('check_access') as span:
        span.set_attribute('request-id', X_Request_Id)
    if user_id:
        user_roles = await user_role_service.get_user_roles(user_id)
    else:
        user_roles = await user_role_service.get_user_roles(decoded_token['user_id'])
    if not user_roles:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='User or role not found')
    return user_roles
