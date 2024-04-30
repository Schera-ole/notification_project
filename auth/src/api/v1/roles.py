'''
CRUD для управления ролями:
создание роли,
удаление роли,
изменение роли,
просмотр всех ролей.
'''
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from opentelemetry import trace
from sqlalchemy.ext.asyncio import AsyncSession

from db.psql import get_session
from schemas.base import HTTPExceptionResponse
from schemas.roles import RoleBase, RoleResponse
from services.role import RoleService, get_role_service
from services.verify import is_admin, security_jwt

tracer = trace.get_tracer(__name__)
router = APIRouter()


@router.post(
    '/',
    response_model=RoleResponse,
    summary='Создание роли',
    responses={
        status.HTTP_400_BAD_REQUEST: {'model': HTTPExceptionResponse},
        status.HTTP_401_UNAUTHORIZED: {'model': HTTPExceptionResponse},
        status.HTTP_403_FORBIDDEN: {'model': HTTPExceptionResponse},
    }
)
async def create_role(
    role_create: RoleBase,
    decoded_token: dict = Depends(security_jwt),
    db_session: AsyncSession = Depends(get_session),
    role_service: RoleService = Depends(get_role_service),
    X_Request_Id: str = Header(...),
) -> RoleResponse:
    is_admin(decoded_token['roles'])
    with tracer.start_span('create_role') as span:
        span.set_attribute('request-id', X_Request_Id)

    if await role_service.get_role_by_name(role_create.name):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Role already exists')
    return await role_service.create_role(role_create)


@router.delete(
    '/{role_id}/',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Удаление роли',
    responses={
        status.HTTP_401_UNAUTHORIZED: {'model': HTTPExceptionResponse},
        status.HTTP_403_FORBIDDEN: {'model': HTTPExceptionResponse},
        status.HTTP_404_NOT_FOUND: {'model': HTTPExceptionResponse},
    }
)
async def delete_role(
    role_id: UUID,
    decoded_token: dict = Depends(security_jwt),
    db_session: AsyncSession = Depends(get_session),
    role_service: RoleService = Depends(get_role_service),
    X_Request_Id: str = Header(...),
) -> None:
    is_admin(decoded_token['roles'])
    with tracer.start_span('delete_role') as span:
        span.set_attribute('request-id', X_Request_Id)

    if not (await role_service.delete_role(role_id)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='Role not found')


@router.patch(
    '/{role_id}/',
    response_model=RoleResponse,
    summary='Изменение роли',
    responses={
        status.HTTP_401_UNAUTHORIZED: {'model': HTTPExceptionResponse},
        status.HTTP_403_FORBIDDEN: {'model': HTTPExceptionResponse},
        status.HTTP_404_NOT_FOUND: {'model': HTTPExceptionResponse},
    }
)
async def patch_role(
    role_id: UUID,
    role_patch: RoleBase,
    decoded_token: dict = Depends(security_jwt),
    db_session: AsyncSession = Depends(get_session),
    role_service: RoleService = Depends(get_role_service),
    X_Request_Id: str = Header(...),
) -> RoleResponse:
    is_admin(decoded_token['roles'])
    with tracer.start_span('patch_role') as span:
        span.set_attribute('request-id', X_Request_Id)

    role = await role_service.patch_role(role_id, role_patch)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='Role not found')
    return role


@router.get(
    '/',
    response_model=list[RoleResponse],
    summary='Список ролей',
    responses={
        status.HTTP_401_UNAUTHORIZED: {'model': HTTPExceptionResponse},
        status.HTTP_403_FORBIDDEN: {'model': HTTPExceptionResponse},
        status.HTTP_404_NOT_FOUND: {'model': HTTPExceptionResponse},
    }
)
async def list_roles(
    decoded_token: dict = Depends(security_jwt),
    db_session: AsyncSession = Depends(get_session),
    role_service: RoleService = Depends(get_role_service),
    X_Request_Id: str = Header(...),
) -> list[RoleResponse]:
    is_admin(decoded_token['roles'])
    with tracer.start_span('list_roles') as span:
        span.set_attribute('request-id', X_Request_Id)

    return await role_service.list_roles()
