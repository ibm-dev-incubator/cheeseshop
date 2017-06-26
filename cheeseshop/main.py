import argparse
import sys

from aiohttp import web
import aiohttp_jinja2
import jinja2

def parse_args(args):
    parser = argparse.ArgumentParser(description='cheeseshop webapp.')
    parser.add_argument('--port', type=int, default=8080,
                        help='port to bind to')
    parser.add_argument('--host', type=str, default='::1',
                        help='host to bind to')
    return parser.parse_args(args)


@aiohttp_jinja2.template('upload.html')
async def handle_upload(request):
    return {}


def main():
    args = parse_args(sys.argv[1:])

    app = web.Application()
    app.router.add_get('/upload', handle_upload)

    aiohttp_jinja2.setup(
        app,
        loader=jinja2.PackageLoader('cheeseshop', 'templates')
    )

    web.run_app(app, host='::', port=args.port)
