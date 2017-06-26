import argparse
import sys

from aiohttp import web

def parse_args(args):
    parser = argparse.ArgumentParser(description='cheeseshop webapp.')
    parser.add_argument('--port', type=int, default=8080,
                        help='port to bind to')
    parser.add_argument('--host', type=str, default='::1',
                        help='host to bind to')
    return parser.parse_args(args)


async def handle(request):
    name = request.match_info.get('name', "Anonymous")
    text = "Hello, " + name
    return web.Response(text=text)


def main():
    args = parse_args(sys.argv[1:])

    app = web.Application()
    app.router.add_get('/', handle)
    app.router.add_get('/{name}', handle)

    web.run_app(app, host='::', port=args.port)
