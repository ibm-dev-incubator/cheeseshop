from enum import Enum
from datetime import datetime
import sys

import asyncpg


class NotFoundError(Exception):
    pass


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
        if row is None:
            raise NotFoundError()
        return Game(row['id'], row['name'], row['description'])

    def __init__(self, id_, name, description):
        self.id = id_
        self.name = name
        self.description = description


class ReplayUploadState(Enum):
    ERROR = 'error'
    UPLOADING_TO_SWIFT = 'uploading_to_swift'
    CLIENT_UPLOADING_TO_SWIFT = 'client_uploading_to_swift'
    COMPLETE = 'complete'


class Replay(object):
    @staticmethod
    async def create_schema(conn):
        await conn.execute('''
            CREATE TYPE replay_upload_state AS ENUM (
                'error',
                'uploading_to_swift',
                'client_uploading_to_swift',
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
        if row is None:
            raise NotFoundError()
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
    async def get_oldest_by_streamer_id(conn, streamer_id,
                                        limit=100, offset=0):
        evs = []
        async for record in conn.cursor('''
            SELECT * FROM cs_go_gsi_events
            WHERE streamer_id = $1
            ORDER BY id ASC
            LIMIT $2
            OFFSET $3
        ''', streamer_id, limit, offset):
            evs.append(CsGoGsiEvent.from_row(record))
        return evs

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
    async def get_by_map_uuid(conn, map_uuid):
        events = []
        async for record in conn.cursor('''
            SELECT * FROM cs_go_gsi_events
            INNER JOIN cs_go_event_map_releation
                ON cs_go_event_map_releation.event_id = cs_go_gsi_events.id
            INNER JOIN cs_go_map
                ON cs_go_event_map_releation.map_id = cs_go_map.id
            WHERE cs_go_map.uuid = $1
        ''', map_uuid):
            events.append(CsGoGsiEvent(
                record['event_id'],
                record['time'],
                record['streamer_id'],
                record['event']
            ))
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


class CsGoHltvEventType(object):
    @staticmethod
    async def create_schema(conn):
        await conn.execute('''
            CREATE TABLE cs_go_hltv_event_types(
                id serial PRIMARY KEY,
                name text UNIQUE NOT NULL
            )
        ''')


class CsGoHltvEvent(object):
    @staticmethod
    async def create_schema(conn):
        await conn.execute('''
            CREATE TABLE cs_go_hltv_events(
                id serial PRIMARY KEY,
                time timestamp,
                replay_id integer REFERENCES replays (id),
                type integer REFERENCES cs_go_hltv_event_types,
                event json
            )
        ''')


class CsGoMap(object):
    @staticmethod
    async def create_schema(conn):
        await conn.execute('''
            CREATE TABLE cs_go_map(
                id serial PRIMARY KEY,
                uuid text UNIQUE,
                start_time timestamp,
                streamer_id integer REFERENCES cs_go_streamer (id),
                map_name text,
                team_1 text,
                team_2 text
            )
        ''')
        await conn.execute('''
            CREATE UNIQUE INDEX ON cs_go_map (uuid)
        ''')

    @staticmethod
    async def create(conn, uuid, start_time, streamer_id, map_name, team_1,
                     team_2):
        row = await conn.fetchrow('''
            INSERT INTO cs_go_map(uuid, start_time, streamer_id, map_name,
                                  team_1, team_2)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
        ''', uuid, start_time, streamer_id, map_name, team_1, team_2)
        return CsGoMap(row['id'], uuid, start_time, streamer_id, map_name,
                       team_1, team_2)

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
        return CsGoMap(row['id'], row['uuid'], row['start_time'],
                       row['streamer_id'], row['map_name'], row['team_1'],
                       row['team_2'])

    def __init__(self, id_, uuid, start_time, streamer_id, map_name, team_1,
                 team_2):
        self.id = id_
        self.uuid = uuid
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

    @staticmethod
    async def create(conn, event_id, map_id):
        await conn.execute('''
            INSERT INTO cs_go_event_map_releation (event_id, map_id)
            VALUES ($1, $2)
        ''', event_id, map_id)
        return CsGoEventMapRelation(event_id, map_id)

    @staticmethod
    async def get_oldest(conn, streamer_id, limit=100, offset=0):
        ev_maps = []
        async for record in conn.cursor('''
            SELECT * FROM cs_go_gsi_events
            INNER JOIN cs_go_event_map_releation ON cs_go_gsi_events.id =
                       cs_go_event_map_releation.event_id
            INNER JOIN cs_go_map ON cs_go_event_map_releation.map_id =
                       cs_go_map.id
            WHERE cs_go_gsi_events.streamer_id = $1
            ORDER BY cs_go_gsi_events.id ASC
            LIMIT $2
            OFFSET $3
        ''', streamer_id, limit, offset):
            ev = CsGoGsiEvent(conn, streamer_id,
                              record['cs_go_gsi_events.time'],
                              record['cs_go_gsi_events.event'])
            map_ = CsGoMap(record['cs_go_map.start_time'],
                           record['cs_go_map.streamer_id'],
                           record['cs_go_map.map_name'],
                           record['cs_go_map.team_1'],
                           record['cs_go_map.team_2'])
            ev_maps.append((ev, map_))
        return ev_maps

    def __init__(self, event_id, map_id):
        self.event_id = event_id
        self.map_id = map_id


async def create_schema(conn):
    await Game.create_schema(conn)
    await Replay.create_schema(conn)
    await CsGoHltvEventType.create_schema(conn)
    await CsGoHltvEvent.create_schema(conn)
    await CsGoStreamer.create_schema(conn)
    await CsGoGsiEvent.create_schema(conn)
    await CsGoMap.create_schema(conn)
    await CsGoEventMapRelation.create_schema(conn)


async def create_initial_records(conn):
    async with conn.transaction():
        await Game.create(conn, 'sc2', 'StarCraft 2')
        await Game.create(conn, 'cs:go', 'Counter Strike: Global Offensive')


async def db_backup(conn):
    tables = ['games', 'replays', 'cs_go_streamer', 'cs_go_gsi_eventsi',
              'cs_go_hltv_event_types', 'cs_go_hltv_events', 'cs_go_map',
              'cs_go_event_map_relation']
    timestamp = str(datetime.now()).replace(' ', '')

    try:
        backup_file = open('cheeseshop_db_' + timestamp + '.sql')
        async for table in tables:
            rows = await conn.execute('''SELECT * FROM $1''', table)
            async for row in rows:
                if row is None:
                    raise NotFoundError()
                backup_file.write(row)
    except asyncpg.PostgresError as e:
        print('ERROR: %s' % e)
        sys.exit(1)
    finally:
        if conn:
            conn.close()
        if backup_file:
            backup_file.close()
