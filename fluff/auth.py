import typing

from httpx import Auth, Request, Response


class BearerAuth(Auth):
    def __init__(self, token):
        self.token = token

    def auth_flow(self, request: Request) -> typing.Generator[Request, Response, None]:
        request.headers['Authorization'] = f'Bearer {self.token}'
        yield request
