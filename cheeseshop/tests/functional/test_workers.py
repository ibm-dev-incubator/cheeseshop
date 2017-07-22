import datetime
import json
import re

from cheeseshop import dbapi
from cheeseshop.tests.functional import base
from cheeseshop.workers import csgo_map_populator


class TestCsGoMapPopulator(base.FunctionalTestCase):
    async def test_run(self):
        gsi_data = {
            'map': {
                'phase': 'live',
                'team_t': {
                    'name': 'team 1'
                },
                'team_ct': {
                    'name': 'team 2'
                },
                'name': 'map name'
            }
        }

        async with self.pool.acquire() as conn:
            streamer = await dbapi.CsGoStreamer.create(conn, 'streamer-uuid',
                                                       'a streamer')
            await dbapi.CsGoGsiEvent.create(conn, datetime.datetime.now(),
                                            streamer.id, json.dumps(gsi_data))
            await dbapi.CsGoGsiEvent.create(conn, datetime.datetime.now(),
                                            streamer.id, json.dumps(gsi_data))

            gsi_data['map']['phase'] = 'gameover'
            await dbapi.CsGoGsiEvent.create(conn, datetime.datetime.now(),
                                            streamer.id, json.dumps(gsi_data))
            await dbapi.CsGoGsiEvent.create(conn, datetime.datetime.now(),
                                            streamer.id, json.dumps(gsi_data))

            gsi_data['map']['phase'] = 'warmup'
            gsi_data['map']['team_t']['name'] = 'team 3'
            gsi_data['map']['team_ct']['name'] = 'team 4'
            gsi_data['map']['name'] = 'map 2 name'
            await dbapi.CsGoGsiEvent.create(conn, datetime.datetime.now(),
                                            streamer.id, json.dumps(gsi_data))
            await dbapi.CsGoGsiEvent.create(conn, datetime.datetime.now(),
                                            streamer.id, json.dumps(gsi_data))

            gsi_data['map']['phase'] = 'live'
            await dbapi.CsGoGsiEvent.create(conn, datetime.datetime.now(),
                                            streamer.id, json.dumps(gsi_data))
            await dbapi.CsGoGsiEvent.create(conn, datetime.datetime.now(),
                                            streamer.id, json.dumps(gsi_data))

            gsi_data['map']['team_t']['name'] = 'team 4'
            gsi_data['map']['team_ct']['name'] = 'team 3'
            await dbapi.CsGoGsiEvent.create(conn, datetime.datetime.now(),
                                            streamer.id, json.dumps(gsi_data))
            await dbapi.CsGoGsiEvent.create(conn, datetime.datetime.now(),
                                            streamer.id, json.dumps(gsi_data))
        await csgo_map_populator.run(self.pool, 'streamer-uuid', 5)

        maps_resp = await self.client.get('/games/csgo/gsi/maps')
        self.assertEqual(maps_resp.status, 200)
        maps_resp_txt = await maps_resp.text()
        self.assertEqual(maps_resp_txt.count(
            '<li>team 1 vs team 2 on map name</li>'
        ), 1)
        self.assertEqual(maps_resp_txt.count(
            '<li>team 3 vs team 4 on map 2 name</li>'
        ), 1)
