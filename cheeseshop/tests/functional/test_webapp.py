from cheeseshop.tests.functional import base


class TestUploads(base.FunctionalTestCase):
    async def test_get_upload(self):
        resp = await self.client.get("/upload")
        resp_text = await resp.text()
        self.assertTrue('<option value="sc2">StarCraft 2</option>'
                        in resp_text)
        self.assertTrue('<option value="cs:go">Counter Strike: Global '
                        'Offensive</option>' in resp_text)
        assert resp.status == 200
