from enum import Enum

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


class ReplayUploadState(Enum):
    ERROR = 'error'
    UPLOADING_TO_SWIFT = 'uploading_to_swift'
    COMPLETE = 'complete'


class Replay(object):
    @staticmethod
    async def create_schema(conn):
        await conn.execute('''
            CREATE TYPE replay_upload_state AS ENUM (
                'error',
                'uploading_to_swift',
                'complete'
            )
        ''')
        await conn.execute('''
            CREATE TABLE replays(
                id serial PRIMARY KEY,
                uuid text UNIQUE NOT NULL,
                game_id integer REFERENCES games (id),
                upload_state replay_upload_state,
                sha1sum text UNIQUE
            )
        ''')
        await conn.execute('''
            CREATE UNIQUE INDEX ON replays (uuid)
        ''')
        await conn.execute('''
            CREATE UNIQUE INDEX ON replays (sha1sum)
        ''')

    @staticmethod
    async def create(conn, uuid, game_id, upload_state, sha1sum):
        row = await conn.fetchrow('''
            INSERT INTO replays(uuid, game_id, upload_state, sha1sum)
            VALUES($1, $2, $3, $4)
            RETURNING id
        ''', uuid, game_id, upload_state.value, sha1sum)
        return Replay(row['id'], uuid, game_id, upload_state, sha1sum)

    @staticmethod
    async def get_all(conn):
        replays = []
        async for record in conn.cursor('''
            SELECT * FROM replays
        '''):
            replays.append(Replay.from_db_row(record))
        return replays

    @staticmethod
    async def get_by_uuid(conn, uuid):
        row = await conn.fetchrow('''
            SELECT * FROM replays WHERE uuid = $1
        ''', uuid)
        return Replay.from_db_row(row)

    @staticmethod
    async def get_by_sha1sum(conn, sha1sum):
        row = await conn.fetchrow('''
            SELECT * FROM replays WHERE sha1sum = $1
        ''', sha1sum)
        return Replay.from_db_row(row)

    @staticmethod
    def from_db_row(row):
        return Replay(row['id'], row['uuid'], row['game_id'],
                      ReplayUploadState(row['upload_state']), row['sha1sum'])


    def __init__(self, id_, uuid, game_id, upload_state, sha1sum):
        self.id = id_
        self.uuid = uuid
        self.game_id = game_id
        self.upload_state = upload_state
        self.sha1sum = sha1sum

    def __eq__(self, other):
        return self.uuid == other.uuid

    async def set_upload_state(self, conn, upload_state):
        await conn.execute('''
            UPDATE replays SET upload_state = $1
            WHERE id = $2
        ''', upload_state.value, self.id)


class CsGoStreamer(object):
    @staticmethod
    async def create_schema(conn):
        await conn.execute('''
            CREATE TABLE cs_go_streamer(
                id serial PRIMARY KEY,
                uuid text UNIQUE NOT NULL,
                name text UNIQUE NOT NULL
            )
        ''')
        await conn.execute('''
            CREATE UNIQUE INDEX ON cs_go_streamer (uuid)
        ''')
        await conn.execute('''
            CREATE UNIQUE INDEX ON cs_go_streamer (name)
        ''')

    @staticmethod
    async def create(conn, uuid, name):
        row = await conn.fetchrow('''
            INSERT INTO cs_go_streamer(uuid, name)
            VALUES($1, $2)
            RETURNING id
        ''', uuid, name)
        return CsGoStreamer(row['id'], uuid, name)

    @staticmethod
    async def get_all(conn):
        streamers = []
        async for record in conn.cursor('''
            SELECT * FROM cs_go_streamer
        '''):
            streamers.append(CsGoStreamer.from_row(record))
        return streamers

    @staticmethod
    async def get_by_name(conn, name):
        row = await conn.fetchrow('''
            SELECT * FROM cs_go_streamer
            WHERE name = $1
        ''', name)
        return CsGoStreamer.from_row(row)

    @staticmethod
    async def get_by_uuid(conn, uuid):
        row = await conn.fetchrow('''
            SELECT * FROM cs_go_streamer
            WHERE uuid = $1
        ''', uuid)
        return CsGoStreamer.from_row(row)

    @staticmethod
    def from_row(row):
        return CsGoStreamer(row['id'], row['uuid'], row['name'])

    def __init__(self, id_, uuid, name):
        self.id = id_
        self.uuid = uuid
        self.name = name


class CsGoGsiEvent(object):
    @staticmethod
    async def create_schema(conn):
        await conn.execute('''
            CREATE TABLE cs_go_gsi_events(
                id serial PRIMARY KEY,
                time timestamp,
                streamer_id integer REFERENCES cs_go_streamer (id),
                event json
            )
        ''')

    @staticmethod
    async def create(conn, time, streamer_id, event):
        row = await conn.fetchrow('''
            INSERT INTO cs_go_gsi_events(time, streamer_id, event)
            VALUES($1, $2, $3)
            RETURNING id, time
        ''', time, streamer_id, event)
        return CsGoGsiEvent(row['id'], row['time'], streamer_id, event)

    @staticmethod
    async def get_by_streamer_id(conn, streamer_id):
        events = []
        async for record in conn.cursor('''
            SELECT * FROM cs_go_gsi_events
            WHERE streamer_id = $1
        ''', streamer_id):
            events.append(CsGoGsiEvent.from_row(record))
        return events

    @staticmethod
    def from_row(row):
        return CsGoGsiEvent(row['id'], row['time'], row['streamer_id'],
                            row['event'])

    def __init__(self, id_, time, streamer_id, event):
        self.id = id_
        self.time = time
        self.streamer_id = streamer_id
        self.event = event


class CsGoMap(object):
    @staticmethod
    async def create_schema(conn):
        await conn.execute('''
            CREATE TABLE cs_go_map(
                id serial PRIMARY KEY,
                start_time timestamp,
                streamer_id integer REFERENCES cs_go_streamer (id),
                map_name text,
                team_1 text,
                team_2 text
            )
        ''')

    @staticmethod
    async def create(conn, start_time, streamer_id, map_name, team_1, team_2):
        row = await conn.fetchrow('''
            INSERT INTO cs_go_map(start_time, streamer_id, map_name, team_1, team_2)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
        ''', start_time, streamer_id, map_name, team_1, team_2)
        return CsGoMap(row['id'], start_time, streamer_id, map_name, team_1, team_2)

    @staticmethod
    async def get_all(conn):
        maps = []
        async for record in conn.cursor('''
            SELECT * from cs_go_map
        '''):
            maps.append(CsGoMap.from_row(record))
        return maps

    @staticmethod
    def from_row(row):
        return CsGoMap(row['id'], row['start_time'], row['streamer_id'],
                       row['map_name'], row['team_1'], row['team_2'])

    def __init__(self, id_, start_time, streamer_id, map_name, team_1, team_2):
        self.id = id_
        self.start_time = start_time
        self.streamer_id = streamer_id
        self.map_name = map_name
        self.team_1 = team_1
        self.team_2 = team_2


class CsGoEventMapRelation(object):
    @staticmethod
    async def create_schema(conn):
        await conn.execute('''
            CREATE TABLE cs_go_event_map_releation(
                event_id integer REFERENCES cs_go_gsi_events (id),
                map_id integer REFERENCES cs_go_map (id)
            )
        ''')

    def __init__(self, event_id, map_id):
        self.event_id = event_id
        self.map_id = map_id


async def create_schema(conn):
    await Game.create_schema(conn)
    await Replay.create_schema(conn)
    await CsGoStreamer.create_schema(conn)
    await CsGoGsiEvent.create_schema(conn)
    await CsGoMap.create_schema(conn)
    await CsGoEventMapRelation.create_schema(conn)


async def create_initial_records(conn):
    async with conn.transaction():
        await Game.create(conn, 'sc2', 'StarCraft 2')
        await Game.create(conn, 'cs:go', 'Counter Strike: Global Offensive')
