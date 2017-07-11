from cheeseshop import dbapi
from cheeseshop.tests.functional import base


class TestDbApi(base.FunctionalTestCase):
    async def test_games(self):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                initial_games = await dbapi.Game.get_all(conn)
                self.assertEqual(len(initial_games), 2)

            my_game = await dbapi.Game.create(conn, 'test_game',
                                              'a test game')
            self.assertEqual(my_game.id, 3)
            my_game2 = await dbapi.Game.create(conn, 'another_game',
                                               'another test game')
            self.assertEqual(my_game2.id, 4)

            async with conn.transaction():
                games = await dbapi.Game.get_all(conn)
                self.assertEqual(len(games), 4)

    async def test_replay(self):
        async with self.pool.acquire() as conn:
            my_game = await dbapi.Game.create(conn, 'test_game',
                                              'a test game')
            my_replay = await dbapi.Replay.create(
                conn,
                'uuid-1234',
                my_game.id,
                dbapi.ReplayUploadState.COMPLETE,
                '1234')

            replay = await dbapi.Replay.get_by_uuid(conn, 'uuid-1234')
            self.assertEqual(replay, my_replay)

            replay = await dbapi.Replay.get_by_sha1sum(conn, '1234')
            self.assertEqual(replay, my_replay)
