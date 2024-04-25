import secrets
import string
from functools import lru_cache

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import select
from yandex_oauth import yao
from yandexid import YandexID, YandexOAuth

from core.settings import yandex_settings
from db.psql import get_session
from models.user import SocialAccount, User


class OAuthLogin(object):
    providers = None

    def __init__(self, provider_name):
        self.provider_name = provider_name

    def get_auth_url(self):
        pass

    @classmethod
    def get_provider(self, provider_name):
        if self.providers is None:
            self.providers = {}
            for provider_class in self.__subclasses__():
                provider = provider_class()
                self.providers[provider.provider_name] = provider
        return self.providers.get(provider_name)


class DbService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_account_in_social(self, social_id, social_name) -> list:
        accounts = await self.db.execute(
            select(User)
            .filter(
                SocialAccount.social_id == social_id,
                SocialAccount.social_name == social_name)
            .join(SocialAccount)
        )

        accounts = [row for row in accounts.scalars()]
        if len(accounts) == 1:
            account = accounts[0]
            user_id = account.id
            email = account.email
            return user_id, email

    @staticmethod
    def __prepare_select_sql_query(
            what_select,
            where_select: list = None,
            order_select=None,
            join_with=None,
    ):
        default_sql = select(what_select)
        if where_select:
            default_sql = default_sql.where(
                where_select[0] == where_select[1]
            )
        if order_select:
            default_sql = default_sql.order_by(order_select())
        if join_with:
            default_sql = default_sql.join(join_with)
        return default_sql

    async def simple_select(
            self,
            what_select,
            where_select: list = None,
            order_select=None,
            join_with=None,
    ):
        sql = self.__prepare_select_sql_query(
            what_select=what_select,
            where_select=where_select,
            order_select=order_select,
            join_with=join_with,
        )

        data = await self.db.execute(sql)
        return [row for row in data.scalars()]

    async def insert_data(self, data) -> None:
        self.db.add(data)
        await self.db.commit()
        await self.db.refresh(data)


class YandexProvider(OAuthLogin):
    def __init__(self, db_service=None) -> None:
        super(YandexProvider, self).__init__("yandex")
        self.yandex_oauth = YandexOAuth(
            client_id=yandex_settings.YANDEX_CLIENT_ID,
            client_secret=yandex_settings.YANDEX_CLIENT_SECRET,
            redirect_uri=yandex_settings.YANDEX_REDIRECT_URI,
        )
        self.db_service = DbService(db=db_service)

    def get_auth_url(self):
        return self.yandex_oauth.get_authorization_url()

    async def register(self, code):
        token = yao.get_token_by_code(
            code,
            yandex_settings.YANDEX_CLIENT_ID,
            yandex_settings.YANDEX_CLIENT_SECRET
        )
        social_user = YandexID(token.get('access_token'))
        user_data = social_user.get_user_info_json()
        account = await self.db_service.check_account_in_social(
            social_id=user_data.psuid,
            social_name='yandex'
        )
        if account:
            return account
        user = await self.db_service.simple_select(
            what_select=User,
            where_select=[User.email, user_data.default_email]
        )
        user_id = None
        email = None
        if len(user) == 1:
            user = user[0]
            user_id = user.id
            email = user.email
        elif len(user) == 0:
            user = User(email=user_data.default_email, password=''.join(
                secrets.choice(string.ascii_letters + string.digits) for i in range(20)
            ))
            await self.db_service.insert_data(data=user)
            user_id = user.id
            email = user.email
        else:
            return None

        social_account = SocialAccount(
            user=user, social_id=user_data.psuid, social_name="yandex"
        )
        await self.db_service.insert_data(data=social_account)
        return user_id, email


@lru_cache()
def yandex_provider(db_service: AsyncSession = Depends(get_session)):
    return YandexProvider(
        db_service=db_service
    )
