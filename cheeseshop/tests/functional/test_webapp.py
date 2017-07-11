from unittest import mock

from aiohttp import FormData

from cheeseshop.tests import fakes
from cheeseshop.tests.functional import base


class TestUploads(base.FunctionalTestCase):
    @mock.patch('swift.KeystoneSession')
    @mock.patch('cheeseshop.main.swift.SwiftClient')
    async def test_upload(self, keystone_session, swift_client):
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

        resp = await self.client.post("/upload", data=data)
        self.assertEqual(resp.status, 200)
