import copy

from cheeseshop import db
from cheeseshop.tests import asyncfixtures, base


class SqlTestFixture(asyncfixtures.AsyncFixture):
    def __init__(self, pool, db_name):
        self.pool = pool
        self.db_name = db_name

    async def _setUp(self):
        async with self.pool.acquire() as conn:
            await conn.execute('CREATE DATABASE "%s"' % self.db_name)

    async def cleanUp(self):
        super(SqlTestFixture, self).cleanUp()
        async with self.pool.acquire() as conn:
            await conn.execute('DROP DATABASE "%s"' % self.db_name)


class FunctionalTestCase(base.TestCase):
    async def setUp(self):
        super(FunctionalTestCase, self).setUp()
        # We need to use db 'postgres' while creating our test db
        db_create_config = copy.deepcopy(self.config)
        db_create_config.sql.database = 'postgres'
        pool = await db.create_pool(db_create_config.sql)
        await self.useAsyncFixture(SqlTestFixture(pool,
                                                  self.config.sql.database))

        self.pool = await db.create_pool(self.config)
