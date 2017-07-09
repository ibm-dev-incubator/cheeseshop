import aiopg
import asyncio

import sqlalchemy as sa

from cheeseshop import config as cs_config

metadata = sa.MetaData()

replays = sa.Table('replays', metadata,
                   sa.Column('id', sa.Integer, sa.Sequence('id_seq'), primary_key=True),
                   sa.Column('sha1sum', sa.String(40)),
                   sa.Column('filename', sa.tString()),
                   )


async def create_schema(conn):
    pass
