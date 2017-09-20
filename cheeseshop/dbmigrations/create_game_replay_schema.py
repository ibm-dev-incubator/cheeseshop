from cheeseshop import dbapi


async def run(conn):
    await dbapi.Game.create_schema(conn)
    await dbapi.Replay.create_schema(conn)
