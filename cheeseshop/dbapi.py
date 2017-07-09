import asyncpg


async def create_schema(conn):
    await conn.execute('''
        CREATE TABLE replays(
            id serial PRIMARY KEY,
            sha1sum text,
            filename text
        )
    ''')

    await conn.execute('''
        CREATE UNIQUE INDEX ON replays (sha1sum)
    ''')


class Replay(object):
    def __init__(self, id_, sha1sum, filename):
        self.id = id_
        self.sha1sum = sha1sum
        self.filename = filename


class DbApi(object):
    def __init__(self, conn):
        self.conn = conn

    async def create_replay(self, sha1sum, filename):
        await self.conn.execute('''
            INSERT INTO replays(sha1sum, filename)
            VALUES($1, $2)
        ''', sha1sum, filename)

    async def get_replay_by_sha1sum(self, sha1sum):
        row = await self.conn.fetchrow('''
            SELECT * FROM replays WHERE sha1sum = $1
        ''', sha1sum)
        return Replay(row['id'], row['sha1sum'], row['filename'])
