import argparse
import asyncio
import sys
import uuid

from aiohttp import web
import aiohttp_jinja2
import jinja2

from cheeseshop import config as cs_config
from cheeseshop import db
from cheeseshop import dbapi
from cheeseshop.games import csgo
from cheeseshop import objectstoreapi
from cheeseshop import swift


def parse_args(args):
    parser = argparse.ArgumentParser(description='cheeseshop webapp.')
    parser.add_argument('config_file', type=str,
                        help='Path to config file')
    return parser.parse_args(args)


class App(object):
    def __init__(self, config, sql_pool):
        self.config = config
        self.sql_pool = sql_pool

        self._csgo_api = csgo.CsGoApi(self.config, self.sql_pool)

    def add_routes(self, router):
        router.add_get('/upload', self.handle_get_upload)
        router.add_post('/upload', self.handle_post_upload)
        router.add_get('/list_replays', self.handle_list_replays)

        self._csgo_api.add_routes(router)

    def run(self):
        web_app = web.Application()
        self.add_routes(web_app.router)

        aiohttp_jinja2.setup(
            web_app,
            loader=jinja2.PackageLoader('cheeseshop', 'templates')
        )

        web.run_app(web_app, host=self.config.host, port=self.config.port)

    @aiohttp_jinja2.template('get_upload.html')
    @db.with_transaction
    async def handle_get_upload(self, conn, request):
        games = await dbapi.Game.get_all(conn)
        return {
            'games': games
        }

    @aiohttp_jinja2.template('post_upload.html')
    async def handle_post_upload(self, request):
        req_data = await request.post()
        replay = None
        async with self.sql_pool.acquire() as conn:
            async with conn.transaction():
                game = await dbapi.Game.get_by_name(conn, req_data['game'])
                replay_uuid = str(uuid.uuid4())
                replay = await dbapi.Replay.create(
                    conn,
                    replay_uuid,
                    game.id,
                    dbapi.ReplayUploadState.UPLOADING_TO_SWIFT,
                    None
                )
        # Swift uploads can take a while so release our db connection
        swift_data = objectstoreapi.ReplayData(
            replay.uuid,
            self.config.swift.replays_container
        )
        async with self._keystone_session() as keystone_session:
            async with self._swift_client(keystone_session) as swift_client:
                await swift_data.set_data(swift_client,
                                          req_data['replay_file'].file.read())

        async with self.sql_pool.acquire() as conn:
            async with conn.transaction():
                await replay.set_upload_state(
                    conn,
                    dbapi.ReplayUploadState.COMPLETE
                )

        return {
            'game': game,
            'replay': replay
        }

    @aiohttp_jinja2.template('list_replays.html')
    @db.with_transaction
    async def handle_list_replays(self, conn, request):
        replays = await dbapi.Replay.get_all(conn)
        return {
            'replays': replays
        }

    def _keystone_session(self):
        swift_config = self.config.swift
        return swift.KeystoneSession(swift_config.auth_url,
                                     swift_config.project_id,
                                     swift_config.user_id,
                                     swift_config.password)

    def _swift_client(self, keystone_session):
        swift_config = self.config.swift
        return swift.SwiftClient(keystone_session,
                                 swift_config.region)


def main():
    args = parse_args(sys.argv[1:])

    config = cs_config.Config.from_yaml_file(args.config_file)

    loop = asyncio.get_event_loop()
    pool = loop.run_until_complete(db.create_pool(config.sql))
    app = App(config, pool)
    app.run()
