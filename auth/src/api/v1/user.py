from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from opentelemetry import trace
from sqlalchemy.ext.asyncio import AsyncSession

from db.psql import get_session
from models.auth_history import AuthHistory
from models.roles import Role
from models.user import User
from schemas.user import UserInDB, UserInput, UserUUID
from services.jwt import JWT
from services.notify import NotifyClient
from services.role import RoleService
from services.user_role import UserRoleService

tracer = trace.get_tracer(__name__)
router = APIRouter()
security = HTTPBearer()


@router.post('/signup/', response_model=UserInDB, status_code=status.HTTP_201_CREATED)
async def register(
    user_input: UserInput,
    db_session: AsyncSession = Depends(get_session),
    X_Request_Id: str = Header(...),
) -> dict:
    """
    Регистрация пользователя
    :return: dict
    """
    with tracer.start_span("signup") as span:
        span.set_attribute("request-id", X_Request_Id)

    user_data = jsonable_encoder(user_input)
    new_user = User(**user_data)
    await new_user.save(db_session)
    default_role = await RoleService(db_session).get_role_by_name('default')
    await UserRoleService(db_session).create_user_role(user_id=new_user.id, role_id=default_role.id)
    await NotifyClient.send_notify(new_user.id)
    return new_user


@router.post('/login/', response_model=dict)
async def login(
    request: Request,
    user_input: UserInput,
    db_session: AsyncSession = Depends(get_session),
    X_Request_Id: str = Header(...),
) -> dict:
    """
    Авторизация пользователя
    :return: dict
    """
    with tracer.start_span("login") as span:
        span.set_attribute("request-id", X_Request_Id)

    user_agent = request.headers.get('user-agent')
    user_data = jsonable_encoder(user_input)
    user: User = await User.get_user(db_session, user_data['email'], user_data['password'])
    permissions = await Role.get_permissions(db_session, user.id)
    new_history_entry = AuthHistory(user_id=user.id, user_agent=user_agent)
    await new_history_entry.save(db_session)

    return await JWT.get_tokens(user.id, permissions)


@router.get('/auth-history/', response_model=dict)
async def auth_history(
    page_size: int,
    page_number: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db_session: AsyncSession = Depends(get_session),
    X_Request_Id: str = Header(...),
) -> dict:
    """
    История авторизаций пользователя
    :return: dict
    """
    with tracer.start_span("auth-history") as span:
        span.set_attribute("request-id", X_Request_Id)

    user: User = await User.get_user_by_token(db_session, credentials.credentials)

    auth_data = await AuthHistory.get_auth_history(db_session, user.id, page_size, page_number)

    result = {
        'history': [
            {
                'timestamp': entry.timestamp.strftime('%d.%m.%Y %H:%M:%S'),
                'user_agent': entry.user_agent
            } for entry in auth_data
        ]
    }

    return result


@router.post('/logout/', response_model=dict)
async def logout(
    db_session: AsyncSession = Depends(get_session),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    X_Request_Id: str = Header(...),
) -> dict:
    """
    Выход из всех аккаунтов по указанному access-токену пользователя
    :return: dict
    """
    with tracer.start_span("logout") as span:
        span.set_attribute("request-id", X_Request_Id)

    user: User = await User.get_user_by_token(db_session, credentials.credentials)

    await user.logout(credentials.credentials)

    return {}


@router.post('/refresh-token/', response_model=dict)
async def refresh_token(
    db_session: AsyncSession = Depends(get_session),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    X_Request_Id: str = Header(...),
) -> dict:
    """
    Обновление токенов юзера и блок переданного refresh токена
    :return: dict
    """
    with tracer.start_span("refresh-token") as span:
        span.set_attribute("request-id", X_Request_Id)

    user: User = await User.get_user_by_token(db_session, credentials.credentials)
    roles = await Role.get_permissions(db_session, user.id)
    await user.logout(credentials.credentials)

    return await JWT.get_tokens(user.id, roles)


@router.get('/get-user-info/', response_model=UserInDB)
async def get_user_info(
    user_id: UserUUID = Depends(),
    db_session: AsyncSession = Depends(get_session),
    X_Request_Id: str = Header(...),
) -> dict:
    """
    Получение информации о пользователе
    :return: dict
    """
    user_input = user_id.model_dump()
    user: User = await User.get_user_by_id(db_session, user_input['user_id'])

    if not user:
        raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='User not found'
            )
    return user
