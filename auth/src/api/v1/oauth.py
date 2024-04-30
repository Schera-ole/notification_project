from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from services.jwt import JWT
from services.oauth import OAuthLogin, YandexProvider, yandex_provider

router = APIRouter()


@router.post(
    '/login/{provider}',
    status_code=200,
    summary="Войти с помощью yandex",
    tags=["Авторизация"],
)
async def provider_login(
    provider: str,
    X_Request_Id: str = Header(...),
):
    provider = OAuthLogin.get_provider(provider)
    if provider:
        return provider.get_auth_url()
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail='Provider was not found'
    )


@router.get(
    '/login/yandex/redirect',
    status_code=status.HTTP_200_OK,
    summary="Войти с помощью яндекса",
    tags=["Авторизация"],
)
async def yandex_login_redirect(
    code: int,
    request: Request,
    yandex_provider: YandexProvider = Depends(yandex_provider),
    auth_service: JWT = Depends(JWT)
):
    login_result = await auth_service.login_by_yandex(
        code=code, yandex_provider=yandex_provider
    )
    if 'access' not in login_result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Error'
        )

    return login_result
