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


def with_connection(f):
    async def new_f(self, request):
        async with self.sql_pool.acquire() as conn:
            return await f(self, conn, request)
    return new_f


def with_transaction(f):
    async def new_f(self, request):
        async with self.sql_pool.acquire() as conn:
            async with conn.transaction():
                return await f(self, conn, request)
    return new_f
