import argparse
import asyncio
import os
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
from cheeseshop import util


def parse_args(args):
    parser = argparse.ArgumentParser(description='cheeseshop webapp.')
    parser.add_argument('config_file', type=str,
                        help='Path to config file')
    parser.add_argument('--create-schema', action='store_true')
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
        router.add_static('/static/',
                          path=os.path.dirname(__file__) + '/static',
                          name='static')

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

    async def handle_post_upload(self, request):
        req_data = await request.post()
        replay = None

        async with self.sql_pool.acquire() as conn:
            async with conn.transaction():
                # If a user supplied a sha and didnt specify overwrite we need
                # to check if the replay already exists
                if ('replay_sha1sum' in req_data
                        and not util.truthy(req_data.get('overwrite'))):
                    try:
                        existing = await dbapi.Replay.get_by_sha1sum(
                            conn, req_data['replay_sha1sum']
                        )
                    except dbapi.NotFoundError:
                        pass
                    else:
                        return web.Response(text='Replay sha1 already exists',
                                            status=409)
                # If we werent supplied a sha1sum then the file must be sent
                elif ('replay_sha1sum' not in req_data
                      and 'replay_file' not in req_data):
                    return web.Response(
                        text='Must specify sha1sum or send file',
                        status=400
                    )

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
                if 'replay_file' in req_data:
                    await swift_data.set_data(
                        swift_client,
                        req_data['replay_file'].file.read()
                    )
                elif 'replay_sha1sum' in req_data:
                    tempurl = await swift_data.create_tempurl(swift_client)
                    context = {
                        'tempurl': tempurl
                    }
                    return aiohttp_jinja2.render_template(
                        'post_upload_tempurl.html',
                        request,
                        context
                    )

        async with self.sql_pool.acquire() as conn:
            async with conn.transaction():
                await replay.set_upload_state(
                    conn,
                    dbapi.ReplayUploadState.COMPLETE
                )

        context = {
            'game': game,
            'replay': replay
        }
        return aiohttp_jinja2.render_template('post_upload_fullreplay.html',
                                              request,
                                              context)

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

    if args.create_schema:
        conn = loop.run_until_complete(pool.acquire())
        loop.run_until_complete(dbapi.create_schema(conn))
        print('DB Schema created')
    else:
        app = App(config, pool)
        app.run()
