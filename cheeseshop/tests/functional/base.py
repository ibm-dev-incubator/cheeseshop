import copy

from cheeseshop import db, dbapi
from cheeseshop.tests import asyncfixtures, base


class FunctionalTestCase(base.TestCase):
    async def setUp(self):
        super(FunctionalTestCase, self).setUp()
        # We need to use db 'postgres' while creating our test db
        db_create_config = copy.deepcopy(self.config)
        db_create_config.sql.database = 'postgres'
        self._create_pool = await db.create_pool(db_create_config.sql)
        async with self._create_pool.acquire() as conn:
            await conn.execute('CREATE DATABASE "%s"'
                               % self.config.sql.database)

        self.pool = await db.create_pool(self.config.sql)

        self.addCleanup(self._cleanup)

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await dbapi.create_schema(conn)

    async def _cleanup(self):
        await self.pool.close()
        async with self._create_pool.acquire() as conn:
            await conn.execute('DROP DATABASE "%s"' % self.config.sql.database)
