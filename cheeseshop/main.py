import argparse
import asyncio
import sys

from aiohttp import web
import aiohttp_jinja2
import jinja2

from cheeseshop import config as cs_config
from cheeseshop import swift
from cheeseshop import dbapi


def parse_args(args):
    parser = argparse.ArgumentParser(description='cheeseshop webapp.')
    parser.add_argument('config_file', type=str,
                        help='Path to config file')
    return parser.parse_args(args)


class App(object):
    def __init__(self, config, sql_pool):
        self.config = config
        self.sql_pool = sql_pool

    def add_routes(self, router):
        router.add_get('/upload', self.handle_get_upload)
        router.add_post('/upload', self.handle_post_upload)
        router.add_get('/list_replays', self.handle_list_replays)
        router.add_get('/test-get-token', self.handle_test_get_token)

    def run(self):
        web_app = web.Application()
        self.add_routes(web_app.router)

        aiohttp_jinja2.setup(
            web_app,
            loader=jinja2.PackageLoader('cheeseshop', 'templates')
        )

        web.run_app(web_app, host=config.host, port=config.port)


    @aiohttp_jinja2.template('get_upload.html')
    async def handle_get_upload(self, request):
        return {}


    @aiohttp_jinja2.template('post_upload.html')
    async def handle_post_upload(self, request):
        engine = request.app['engine']
        replay = {
                "sha1sum": "1c67012fee309bd3d2d68e3d0413c11834133c08",
                "filename": "Hype Replay Neeb vs Byun.SC2Replay"
                }
        async with engine.acquire() as conn:
            await conn.execute(dbapi.replays.insert().values(replay))

        return {}


    async def handle_list_replays(self, request):
        engine = request.app['engine']
        body = '<html><body>'
        async with engine.acquire() as conn:
            async for row in conn.execute(dbapi.replays.select()):
                body += '<p>{}: {}</p>\n'.format(row.sha1sum, row.filename)
            body += "</body></html>"
        return web.Response(body=body)


    async def handle_test_get_token(self, request):
        swift_config = self.config.swift
        async with swift.KeystoneSession(swift_config.auth_url,
                                         swift_config.project_id,
                                         swift_config.user_id,
                                         swift_config.password) as k_s:
            async with swift.SwiftClient(k_s, swift_config.region) as s_c:
                await s_c.create_object('hello-world', 'some data',
                                        'greghaynes-dev')
        return {}


def main():
    args = parse_args(sys.argv[1:])

    config = cs_config.Config.from_yaml_file(args.config_file)

    loop = asyncio.get_event_loop()
    pool = loop.run_until_complete(db.create_pool(config.sql))
    app = App(config, pool)
    app.run()
