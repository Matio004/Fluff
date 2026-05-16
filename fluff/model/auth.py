from abc import abstractmethod, ABC
from typing import Literal

from httpx import Auth, BasicAuth, DigestAuth
from pydantic import BaseModel, Field

from fluff.auth import BearerAuth


class AuthModel(BaseModel):
    type: Literal['bearer_token', 'basic', 'digest'] | None = Field(default=None)
    auth: AuthDataModel | None = Field(default=None)

    @classmethod
    def bearer_token(cls, token: str) -> AuthModel:
        return cls(type='bearer_token', auth=BearerAuthDataModel(token=token))

    @classmethod
    def basic(cls, username: str, password: str) -> AuthModel:
        return cls(type='basic', auth=BasicAuthDataModel(username=username, password=password))

    @classmethod
    def digest(cls, username: str, password: str) -> AuthModel:
        return cls(type='digest', auth=DigestAuthDataModel(username=username, password=password))


class AuthDataModel(BaseModel, ABC):

    @property
    @abstractmethod
    def credentials(self) -> Auth:
        pass


class BearerAuthDataModel(AuthDataModel):
        token: str = Field(default='')

        @property
        def credentials(self) -> Auth:
            return BearerAuth(token=self.token)


class BasicAuthDataModel(AuthDataModel):
    username: str = Field(default='')
    password: str = Field(default='')

    @property
    def credentials(self) -> Auth:
        return BasicAuth(username=self.username, password=self.password)


class DigestAuthDataModel(AuthDataModel):
    username: str = Field(default='')
    password: str = Field(default='')

    @property
    def credentials(self) -> Auth:
        return DigestAuth(username=self.username, password=self.password)
