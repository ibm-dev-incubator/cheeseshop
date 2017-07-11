import asyncio
import copy

from aiohttp import web
from aiohttp.test_utils import TestClient
import aiohttp_jinja2
import jinja2

from cheeseshop import db, dbapi
from cheeseshop import main as cs_main
from cheeseshop.tests import asyncfixtures, base


class FunctionalTestCase(base.TestCase):
    async def setUp(self):
        super(FunctionalTestCase, self).setUp()
        await self._create_db()
        self.app = self.make_app()
        self.client = TestClient(self.app, loop=self.loop)
        await self.client.start_server()

    def make_app(self):
        app = cs_main.App(self.config, self.pool)
        web_app = web.Application()
        app.add_routes(web_app.router)

        aiohttp_jinja2.setup(
            web_app,
            loader=jinja2.PackageLoader('cheeseshop', 'templates')
        )

        return web_app

    async def _create_db(self):
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
                await dbapi.create_initial_records(conn)

    async def _cleanup_db(self):
        await self.pool.close()
        async with self._create_pool.acquire() as conn:
            await conn.execute('DROP DATABASE "%s"' % self.config.sql.database)

    async def _cleanup(self):
        await self._cleanup_db()
        await self.client.close()
