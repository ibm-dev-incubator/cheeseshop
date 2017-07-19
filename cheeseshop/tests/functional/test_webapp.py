import re

from aiohttp import FormData
import fixtures

from cheeseshop.tests import fakes
from cheeseshop.tests.functional import base


class TestUploads(base.FunctionalTestCase):
    async def test_upload(self):
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


class TestCsGo(base.FunctionalTestCase):
    async def test_streamer(self):
        resp = await self.client.get("/games/csgo/gsi/sources")
        self.assertEqual(resp.status, 200)

        data = FormData()
        data.add_field('source_name', 'test_source')

        resp = await self.client.post("/games/csgo/gsi/sources",
                                      data=data)
        self.assertEqual(resp.status, 200)
        resp_text = await resp.text()
        uuid = re.search('Source UUID: (.*)</p>', resp_text).group(1)
        source_url = re.search('URL for GSI config: (.*)</p>',
                               resp_text).group(1)

        resp = await self.client.get("/games/csgo/gsi/sources")
        self.assertEqual(resp.status, 200)
        resp_text = await resp.text()
        self.assertTrue(re.search(uuid, resp_text))
