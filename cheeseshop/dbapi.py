import asyncpg


class Game(object):
    @staticmethod
    async def create_schema(conn):
        await conn.execute('''
            CREATE TABLE games(
                id serial PRIMARY KEY,
                name text UNIQUE,
                description text
            )
        ''')

    @staticmethod
    async def create(conn, name, description):
        row = await conn.fetchrow('''
            INSERT INTO games(name, description)
            VALUES($1, $2)
            RETURNING id
        ''', name, description)
        return Game(row['id'], name, description)

    @staticmethod
    async def get_all(conn):
        games = []
        async for record in conn.cursor('''
            SELECT * FROM games
        '''):
            games.append(Game(record['id'], record['name'],
                              record['description']))
        return games

    @staticmethod
    async def get_by_name(conn, name):
        row = await conn.fetchrow('''
            SELECT * FROM games
            WHERE name = $1
        ''', name)
        return Game(row['id'], row['name'], row['description'])

    def __init__(self, id_, name, description):
        self.id = id_
        self.name = name
        self.description = description


class Replay(object):
    @staticmethod
    async def create_schema(conn):
        await conn.execute('''
            CREATE TABLE replays(
                id serial PRIMARY KEY,
                uuid text UNIQUE NOT NULL,
                game_id integer REFERENCES games (id),
                sha1sum text UNIQUE
            )
        ''')
        await conn.execute('''
            CREATE UNIQUE INDEX ON replays (sha1sum)
        ''')

    @staticmethod
    async def create(conn, uuid, game_id, sha1sum):
        row = await conn.fetchrow('''
            INSERT INTO replays(uuid, game_id, sha1sum)
            VALUES($1, $2, $3)
            RETURNING id
        ''', uuid, game_id, sha1sum)
        return Replay(row['id'], uuid, game_id, sha1sum)

    @staticmethod
    async def get_by_uuid(conn, uuid):
        row = await conn.fetchrow('''
            SELECT * FROM replays WHERE uuid = $1
        ''', uuid)
        return Replay(row['id'], row['uuid'], row['game_id'], row['sha1sum'])

    @staticmethod
    async def get_by_sha1sum(conn, sha1sum):
        row = await conn.fetchrow('''
            SELECT * FROM replays WHERE sha1sum = $1
        ''', sha1sum)
        return Replay(row['id'], row['uuid'], row['game_id'], row['sha1sum'])

    def __init__(self, id_, uuid, game_id, sha1sum):
        self.id = id_
        self.uuid = uuid
        self.game_id = game_id
        self.sha1sum = sha1sum

    def __eq__(self, other):
        return self.uuid == other.uuid


async def create_schema(conn):
    await Game.create_schema(conn)
    await Replay.create_schema(conn)


async def create_initial_records(conn):
    async with conn.transaction():
        await Game.create(conn, 'sc2', 'StarCraft 2')
        await Game.create(conn, 'cs:go', 'Counter Strike: Global Offensive')
