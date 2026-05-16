from collections import defaultdict
from pathlib import Path
from typing import Literal, get_args

import httpx
from pydantic import BaseModel, Field, AnyUrl

from .auth import AuthModel

RequestMethod = Literal['get', 'head', 'post', 'put', 'delete', 'options', 'patch']
REQUEST_METHODS = get_args(RequestMethod)


class RequestModel(BaseModel):
    name: str = Field(default='')
    description: str = Field(default='')
    path: Path | None = Field(default=None, exclude=True)

    url: AnyUrl  # todo change to string
    query_params: list[QueryParamModel] = Field(default_factory=list)
    method: RequestMethod
    headers: list[HeaderModel] = Field(default_factory=list)
    body: BodyModel | None = Field(default=None)
    auth: AuthModel | None = Field(default=None)
    cookies: list[CookieModel] = Field(default_factory=list, exclude=True)

    def to_httpx(self, client: httpx.AsyncClient) -> httpx.Request:
        return client.build_request(
            method=self.method,
            url=str(self.url),
            **(self.body.httpx_kwargs if self.body else {}),
            params=httpx.QueryParams([(param.name, param.value) for param in self.query_params if param.enabled]),
            headers=httpx.Headers([(header.name, header.value) for header in self.headers if header.enabled]),
            cookies=httpx.Cookies([(cookie.name, cookie.value) for cookie in self.cookies if cookie.enabled]),
            # todo timeout
        )


class ItemModel(BaseModel):
    name: str
    value: str
    enabled: bool = Field(default=False)


class HeaderModel(ItemModel):
    pass

class QueryParamModel(ItemModel):
    pass


class CookieModel(ItemModel):
    pass


class BodyModel(BaseModel):
    data: list[ItemModel] | None = Field(default=None)

    content: str | None = Field(default=None)
    content_type: str | None = Field(default=None)

    @property
    def httpx_kwargs(self):
        kwargs = {}

        if self.content:
            kwargs['content'] = self.content

        if self.data:
            data = defaultdict(list)
            for item in self.data:
                data[item.name].append(item.value)
            kwargs['data'] = data
        return kwargs
