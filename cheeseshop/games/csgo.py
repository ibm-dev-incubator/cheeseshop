import asyncio
from concurrent.futures import FIRST_COMPLETED
import json

from aiohttp import web
import aiohttp_jinja2

from cheeseshop.games import gameapi

class GsiPlayer(object):
    def __init__(self, request, gsi_id):
        self._request = request
        self._gsi_id = gsi_id
        self._ws = None

    async def handle(self):
        self._ws = web.WebSocketResponse()
        await self.ws.prepare(self._request)

        send_task = asyncio.ensure_future(self._send())
        listen_task = asyncio.ensure_future(self._listen())

        done, pending = await asyncio.wait((send_task, listen_task),
                                           return_when=FIRST_COMPLETED)
        for task in pending:
            task.cancel()

        return self._ws

    async def _send(self):
        while True:
            self._ws.send_str('hello')
            asyncio.sleep(1)

    async def _listen(self):
        async for msg in self._ws:
            pass


class CsGoApi(gameapi.GameApi):
    def add_routes(self, router):
        router.add_post('/games/csgo/gsi/{streamer_id}/input',
                        self._handle_input_gsi)
        router.add_get('/games/csgo/gsi/{streamer_id}/play',
                       self._handle_play_gsi)

    @aiohttp_jinja2.template('get_upload.html')
    async def _handle_input_gsi(self, request):
        gsi_data = await request.json()
        print()
        print()
        print(json.dumps(gsi_data, indent=4, sort_keys=True))
        print()
        print('======================================')
        print()
        return {}

    async def _handle_play_gsi(self, request):
        gsi_id = request.match_info.get('gsi_id')
        return await GsiPlayer(request, gsi_id).handle()
