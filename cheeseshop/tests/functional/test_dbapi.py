from cheeseshop import dbapi
from cheeseshop.tests.functional import base


class TestSchema(base.FunctionalTestCase):
    async def test_create_replay(self):
        replay = None
        async with self.pool.acquire() as conn:
            db = dbapi.DbApi(conn)
            await db.create_replay('1234', 'file')
            replay = await db.get_replay_by_sha1sum('1234')
        self.assertEqual(replay.filename, 'file')
