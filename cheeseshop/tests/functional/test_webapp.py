import re
from urllib.parse import urlparse
from urllib.parse import parse_qs

from aiohttp import FormData
import fixtures

from cheeseshop.tests import fakes
from cheeseshop.tests.functional import base


class TestUploads(base.FunctionalTestCase):
    async def test_upload_success(self):
        resp = await self.client.get("/upload")
        self.assertEqual(resp.status, 200)
        resp_text = await resp.text()
        self.assertTrue('<option value="sc2">StarCraft 2</option>'
                        in resp_text)
        self.assertTrue('<option value="cs:go">Counter Strike: Global '
                        'Offensive</option>' in resp_text)

        data = FormData()
        data.add_field('game', 'sc2')
        data.add_field('replay_file',
                       b'aaaaaaaaaaaa',
                       filename='test.replay',
                       content_type='text/ascii')

        with fixtures.MonkeyPatch('cheeseshop.swift.KeystoneSession',
                                  fakes.FakeKeystoneSession):
            with fixtures.MonkeyPatch('cheeseshop.swift.SwiftClient',
                                      fakes.FakeSwiftClient):
                resp = await self.client.post("/upload", data=data)
                resp_text = await resp.text()
                self.assertEqual(resp.status, 200)

        # test that we stored the replay in swift
        uuid = re.search('UUID: (.*)</li>', resp_text).group(1)
        self.assertEqual(fakes.get_swift_object(uuid, 'replays_container'),
                         b'aaaaaaaaaaaa')

        # test that the replay shows up in replay list
        resp = await self.client.get("/list_replays")
        self.assertEqual(resp.status, 200)
        resp_text = await resp.text()
        self.assertTrue(re.search(uuid, resp_text))

    async def test_upload_conflicts(self):
        data = FormData()
        data.add_field('game', 'cs:go')
        data.add_field('replay_sha1sum', 'replay_sha1sum')

        # First time should succeed
        with fixtures.MonkeyPatch('cheeseshop.swift.KeystoneSession',
                                  fakes.FakeKeystoneSession):
            with fixtures.MonkeyPatch('cheeseshop.swift.SwiftClient',
                                      fakes.FakeSwiftClient):
                resp = await self.client.post("/upload", data=data)
                resp_text = await resp.text()
                self.assertEqual(resp.status, 200)

        # Second time should fail with 409
        with fixtures.MonkeyPatch('cheeseshop.swift.KeystoneSession',
                                  fakes.FakeKeystoneSession):
            with fixtures.MonkeyPatch('cheeseshop.swift.SwiftClient',
                                      fakes.FakeSwiftClient):
                resp = await self.client.post("/upload", data=data)
                resp_text = await resp.text()
                self.assertEqual(resp.status, 409)

    async def test_swift_tempurl_gen(self):
        data = FormData()
        data.add_field('game', 'cs:go')
        data.add_field('replay_sha1sum', 'replay_sha1sum')

        with fixtures.MonkeyPatch('cheeseshop.swift.KeystoneSession',
                                  fakes.FakeKeystoneSession):
            with fixtures.MonkeyPatch('cheeseshop.swift.SwiftClient',
                                      fakes.FakeSwiftClient):
                with fixtures.MonkeyPatch('hmac.new',
                                          fakes.FakeHmac):
                    resp = await self.client.post("/upload", data=data)
                    resp_text = await resp.text()
                    self.assertEqual(resp.status, 200)
                    tempurl = re.search(
                        'swift tempurl: (.*)</li>', resp_text
                    ).group(1)

                    parsed = urlparse(tempurl)
                    queries = parse_qs(parsed)

                    self.assertEqual(parsed.netloc,
                                     'swift.herpderp.com')
                    self.assertEqual(queries['temp_url_sig'],
                                     'DAEDBEFFCAFE')


class TestCsGoGsi(base.FunctionalTestCase):
    async def test_streamer(self):
        uuid = await self._create_source()
        resp = await self.client.get("/games/csgo/gsi/sources")
        self.assertEqual(resp.status, 200)
        resp_text = await resp.text()
        self.assertTrue(re.search(uuid, resp_text))

        source_base_uri = self._get_source_base_uri(uuid)
        ws_uri = source_base_uri + 'play'
        ws = await self.client.ws_connect(ws_uri)

        gsi_data = {'test-key': 'test-val'}
        await self.client.post(source_base_uri + 'input', json=gsi_data)

        resp = await self.client.get(source_base_uri + 'replay')
        self.assertEqual(resp.status, 200)
        replay_data = await resp.json()
        self.assertEqual(len(replay_data), 1)
        self.assertEqual(replay_data[0]['event'], gsi_data)

        ws_recv = await ws.receive()
        self.assertEqual(ws_recv.json(), gsi_data)

        ws2 = await self.client.ws_connect(ws_uri)
        gsi_data = {'test-key': 'test-val-2'}
        await self.client.post(source_base_uri + 'input', json=gsi_data)

        ws_recv = await ws.receive()
        self.assertEqual(ws_recv.json(), gsi_data)
        ws_recv = await ws2.receive()
        self.assertEqual(ws_recv.json(), gsi_data)

        await ws.close()

        gsi_data = {'test-key': 'test-val-3'}
        await self.client.post(source_base_uri + 'input', json=gsi_data)
        ws_recv = await ws2.receive()
        self.assertEqual(ws_recv.json(), gsi_data)

        await ws2.close()

    async def _get_maps(self):
        maps_resp = await self.client.get('/games/csgo/gsi/maps')
        self.assertEqual(maps_resp.status, 200)
        maps_resp_txt = await maps_resp.text()
        return re.findall('<li>.*UUID: (.*) <a.*', maps_resp_txt)

    async def test_streamer_map_change(self):
        src_uuid = await self._create_source()
        # source_base_uri = self._get_source_base_uri(src_uuid)

        # We shouldnt have any maps detected yet
        self.assertFalse(await self._get_maps())

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
        resp = await self._send_gsi(src_uuid, gsi_data)
        self.assertEqual(resp.status, 200)

        # We should have created a new map
        maps = await self._get_maps()
        self.assertTrue(maps)
        self.assertEqual(len(maps), 1)

        maps_resp = await self.client.get('/games/csgo/gsi/maps')
        self.assertEqual(maps_resp.status, 200)

        gsi_data['map']['phase'] = 'gameover'
        resp = await self._send_gsi(src_uuid, gsi_data)
        self.assertEqual(resp.status, 200)

        gsi_data['map']['phase'] = 'live'
        resp = await self._send_gsi(src_uuid, gsi_data)
        self.assertEqual(resp.status, 200)

        map_uuids = await self._get_maps()
        maps_base_uri = '/games/csgo/gsi/maps'
        replay_uri = '%s/%s/replay' % (maps_base_uri, map_uuids[0])
        replay_req = await self.client.get(replay_uri)
        replay_events = await replay_req.json()
        self.assertEqual(len(replay_events), 2)

    async def _create_source(self):
        resp = await self.client.get("/games/csgo/gsi/sources")
        self.assertEqual(resp.status, 200)

        data = FormData()
        data.add_field('source_name', 'test_source')

        resp = await self.client.post("/games/csgo/gsi/sources",
                                      data=data)
        self.assertEqual(resp.status, 200)
        resp_text = await resp.text()
        uuid = re.search('Source UUID: (.*)</p>', resp_text).group(1)
        self.assertTrue(re.search('URL for GSI config: (.*)</p>', resp_text))
        return uuid

    def _get_source_base_uri(self, source_uuid):
        return '/games/csgo/gsi/sources/%s/' % source_uuid

    async def _send_gsi(self, uuid, gsi_data):
        uri = self._get_source_base_uri(uuid) + 'input'
        return await self.client.post(uri, json=gsi_data)
