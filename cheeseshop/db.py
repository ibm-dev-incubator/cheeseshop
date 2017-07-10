import asyncpg


async def create_pool(config):
    return await asyncpg.create_pool(
        database=config.database,
        user=config.user,
        password=config.password,
        host=config.host,
        port=config.port,
        min_size=config.minsize,
        max_size=config.maxsize
    )
