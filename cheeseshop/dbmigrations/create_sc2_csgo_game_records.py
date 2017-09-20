from cheeseshop import dbapi


async def run(conn):
    async with conn.transaction():
        await dbapi.Game.create(conn, 'sc2', 'StarCraft 2')
        await dbapi.Game.create(conn, 'cs:go',
                                'Counter Strike: Global Offensive')
