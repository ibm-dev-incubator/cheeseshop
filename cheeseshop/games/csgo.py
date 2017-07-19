import asyncio
import collections
from concurrent.futures import FIRST_COMPLETED
import json

from aiohttp import web
import aiohttp_jinja2

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
        router.add_post('/games/csgo/gsi/{streamer_id}/input',
                        self._handle_input_gsi)
        router.add_get('/games/csgo/gsi/{streamer_id}/play',
                       self._handle_play_gsi)

    @aiohttp_jinja2.template('get_upload.html')
    async def _handle_input_gsi(self, request):
        streamer_id = request.match_info.get('streamer_id')
        gsi_data = await request.json()
        for player in self._gsi_players[streamer_id]:
            await player.handle_event(gsi_data)
        print()
        print()
        print(json.dumps(gsi_data, indent=4, sort_keys=True))
        print()
        print('======================================')
        print()
        return {}

    @aiohttp_jinja2.template('handle_play.html')
    async def _handle_play_gsi(self, request):
        print ('=')
        streamer_id = request.match_info.get('streamer_id')
        player = GsiPlayer(request,  streamer_id)
        try:
            self._gsi_players[streamer_id].append(player)
            #return await player.handle()
        finally:
            self._gsi_players[streamer_id].remove(player)
        return {}
