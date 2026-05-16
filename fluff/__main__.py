import argparse
import asyncio
import json
import os
import sys
from urllib import parse
from typing import Collection, get_args

from httpx import AsyncClient
from rich import print_json, print
from rich.console import Console
from rich.pager import Pager, SystemPager

from fluff.auth import BearerAuth
from fluff.model import BodyModel, RequestModel, QueryParamModel, HeaderModel, RequestMethod, REQUEST_METHODS, \
    ItemModel, AuthModel


class KwargsAction(argparse.Action):
    def __call__(self, parser, namespace, values: Collection[str], option_string=None):
        setattr(namespace, self.dest, {})

        for item in values:
            try:
                key, value = item.split('=')
                getattr(namespace, self.dest)[key] = value
            except ValueError:
                parser.error(f'Invalid format for {option_string}: {item}')


class UrlAction(argparse.Action):
    def __call__(self, parser, namespace, values: str, option_string=None):
        url = parse.urlparse(values)
        if not url.scheme:
            if not url.netloc:
                values = '//' + values.removeprefix('://')
            values = 'http:' + values
        url = parse.urlsplit(values, allow_fragments=False)
        setattr(namespace, self.dest, parse.urlunsplit(url))


class ConditionalPager(Pager):
    def __init__(self, console):
        self.console = console

    def show(self, content: str) -> None:
        lines_count = content.count('\n')

        terminal_height = self.console.size.height

        if lines_count < (terminal_height - 1):
            sys.stdout.write(content)
        else:
            pager = SystemPager()
            pager.show(content)


async def main(args):
    client =  AsyncClient(auth=BearerAuth(args.auth))

    method: RequestMethod = args.method
    url = args.url
    query = args.query
    body = args.body
    headers = args.headers
    auth = args.auth
    verbose = args.verbose

    if method is None:
        if args.body:
            method = 'post'
        else:
            method = 'get'

    if query:
        query = [QueryParamModel(name=k, value=v) for k, v in args.query.items()]
    else:
        query = []

    if body:
        body = BodyModel(
            data=[ItemModel(name=k, value=v) for k, v in args.body.items()],
        )
    else:
        body = BodyModel()

    if headers:
        headers = [HeaderModel(name=k, value=v) for k, v in args.query.items()]
    else:
        headers = []

    if auth:
        auth = AuthModel.bearer_token(auth)


    request_model = RequestModel(
        url=url,
        method=method,
        query_params=query,
        headers=headers,
        body=body,
        auth=auth
    )
    request = request_model.to_httpx(client)
    response = await client.send(request)

    console = Console()
    with console.pager(ConditionalPager(console), styles=True):
        console.print(f'Status: {response.status_code} {response.request.method}')
        if verbose > 0:
            console.print('Headers:')
            console.print_json(data=dict(response.headers), indent=4)
        console.print('Body:')
        console.print_json(data=response.json(), indent=4)  # todo add to config

parser = argparse.ArgumentParser()
parser.add_argument('-m', '--method', required=False,
                    choices=REQUEST_METHODS, help='Request method')
parser.add_argument('-u', '--url', required=True, action=UrlAction, help='Url address for request')  # todo url validation

parser.add_argument('-q', '--query', required=False, nargs=argparse.ONE_OR_MORE, action=KwargsAction)
parser.add_argument('-b', '--body', required=False, nargs=argparse.ONE_OR_MORE, action=KwargsAction, help='Request body')
parser.add_argument('-d', '--headers', nargs=argparse.ONE_OR_MORE, action=KwargsAction, required=False, help='Request headers')
parser.add_argument('-a', '--auth', required=False, help='Request auth JWT')
parser.add_argument('-v', '--verbose', required=False, action='count', default=0, help='Verbosity level')
# parser.add_argument('-f', '--file', action='store_false', help='Provide file path') todo implement
args = parser.parse_args()
asyncio.run(main(args))
