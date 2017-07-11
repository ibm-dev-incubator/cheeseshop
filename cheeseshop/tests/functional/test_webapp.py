from aiohttp import FormData

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
        resp = await self.client.post("/upload", data=data)
        self.assertEqual(resp.status, 200)
