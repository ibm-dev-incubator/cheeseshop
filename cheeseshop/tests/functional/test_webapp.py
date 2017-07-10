from cheeseshop.tests.functional import base


class TestUploads(base.FunctionalTestCase):
    async def test_get_upload(self):
        resp = await self.client.get("/upload")
        assert resp.status == 200
