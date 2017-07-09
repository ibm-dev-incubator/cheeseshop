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

