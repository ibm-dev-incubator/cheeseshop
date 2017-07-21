import asyncio
import collections
from concurrent.futures import FIRST_COMPLETED
import datetime
import json
import uuid

from aiohttp import web
import aiohttp_jinja2

from cheeseshop import db
from cheeseshop import dbapi
from cheeseshop.games import gameapi


class GsiPlayer(object):
    def __init__(self, request, streamer_id):
        self._request = request
        self._streamer_id = streamer_id
        self._ws = None
        self._event_queue = asyncio.Queue(maxsize=20)

    async def handle(self):
        self._ws = web.WebSocketResponse()
        await self._ws.prepare(self._request)

        send_task = asyncio.ensure_future(self._send())
        listen_task = asyncio.ensure_future(self._listen())

        done, pending = await asyncio.wait((send_task, listen_task),
                                           return_when=FIRST_COMPLETED)
        for task in pending:
            task.cancel()

        return self._ws

    async def handle_event(self, gsi_event):
        await self._event_queue.put(gsi_event)

    async def _send(self):
        while True:
            self._ws.send_json(await self._event_queue.get())

    async def _listen(self):
        async for msg in self._ws:
            pass


class CsGoApi(gameapi.GameApi):
    def __init__(self, config, sql_pool):
        super(CsGoApi, self).__init__(config, sql_pool)
        self._gsi_players = collections.defaultdict(list)

    def add_routes(self, router):
        router.add_post('/games/csgo/gsi/sources/{streamer_uuid}/input',
                        self._handle_input_gsi)
        router.add_get('/games/csgo/gsi/sources/{streamer_uuid}/play',
                       self._handle_play_gsi)
        router.add_get('/games/csgo/gsi/sources/{streamer_uuid}/replay',
                       self._handle_replay_gsi)
        router.add_get('/games/csgo/gsi/sources',
                       self._handle_get_gsi_source)
        router.add_post('/games/csgo/gsi/sources',
                        self._handle_post_gsi_source)
        router.add_get('/games/csgo/gsi/sources/{streamer_uuid}/deathlog',
                       self._handle_gsi_deathlog)

    @aiohttp_jinja2.template('csgo_deathlog.html')
    async def _handle_gsi_deathlog(self, request):
        streamer_uuid = request.match_info.get('streamer_uuid')
        ws_url = '/games/csgo/gsi/sources/%s/play' % streamer_uuid
        return {
            'gsi_websocket_url': ws_url
        }

    @aiohttp_jinja2.template('get_upload.html')
    @db.with_transaction
    async def _handle_input_gsi(self, conn, request):
        streamer_uuid = request.match_info.get('streamer_uuid')
        gsi_data = await request.json()

        streamer = await dbapi.CsGoStreamer.get_by_uuid(conn, streamer_uuid)
        event = await dbapi.CsGoGsiEvent.create(conn,
                                                datetime.datetime.now(),
                                                streamer.id,
                                                json.dumps(gsi_data))

        for player in self._gsi_players[streamer_uuid]:
            await player.handle_event(gsi_data)
        print()
        print()
        print(json.dumps(gsi_data, indent=4, sort_keys=True))
        print()
        print('======================================')
        print()
        return {}

    async def _handle_play_gsi(self, request):
        streamer_uuid = request.match_info.get('streamer_uuid')
        player = GsiPlayer(request, streamer_uuid)
        try:
            self._gsi_players[streamer_uuid].append(player)
            return await player.handle()
        finally:
            self._gsi_players[streamer_uuid].remove(player)

    @db.with_transaction
    async def _handle_replay_gsi(self, conn, request):
        streamer_uuid = request.match_info.get('streamer_uuid')
        streamer = await dbapi.CsGoStreamer.get_by_uuid(conn, streamer_uuid)
        events = await dbapi.CsGoGsiEvent.get_by_streamer_id(conn, streamer.id)
        dict_events = []
        for event in events:
            time_str = str(event.time)
            dict_events.append({
                'time': time_str,
                'event': json.loads(event.event)
            })
        return web.json_response(dict_events)

    @aiohttp_jinja2.template('get_gsi.html')
    @db.with_transaction
    async def _handle_get_gsi_source(self, conn, request):
        streamers = await dbapi.CsGoStreamer.get_all(conn)
        return {
            'streamers': streamers
        }

    @aiohttp_jinja2.template('post_gsi_source.html')
    @db.with_transaction
    async def _handle_post_gsi_source(self, conn, request):
        req_data = await request.post()
        name = req_data['source_name']
        streamer_uuid = uuid.uuid4()
        streamer = await dbapi.CsGoStreamer.create(conn, str(streamer_uuid),
                                                   name)
        return {
            'streamer': streamer,
            'streamer_gsi_url': self._url_for_streamer(streamer)
        }

    def _url_for_streamer(self, streamer):
        return (self.config.base_uri +
                '/games/csgo/gsi/sources/%s/input' % streamer.uuid)
