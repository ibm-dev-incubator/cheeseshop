import argparse
import asyncio
import json
import sys

from cheeseshop import config as cs_config
from cheeseshop import db
from cheeseshop import dbapi
from cheeseshop.games import csgo


def parse_args(args):
    parser = argparse.ArgumentParser(description='cheeseshop webapp.')
    parser.add_argument('config_file', type=str,
                        help='Path to config file')
    parser.add_argument('streamer_uuid', type=str)
    return parser.parse_args(args)


async def run(db_pool, streamer_uuid):
    stride = 100
    offset = 0
    async with db_pool.acquire() as conn:
        streamer = await dbapi.CsGoStreamer.get_by_uuid(conn, streamer_uuid)
        map_state = csgo.MapState()
        while True:
            async with conn.transaction():
                ret = await dbapi.CsGoGsiEvent.get_oldest_by_streamer_id(
                    conn,
                    streamer.id,
                    limit=stride,
                    offset=offset
                )
                offset += stride
                print('Processing %d events' % len(ret))
                for event in ret:
                    await map_state.update(json.loads(event.event), conn,
                                           streamer)
                if len(ret) < stride: 
                    return


def main():
    args = parse_args(sys.argv[1:])
    config = cs_config.Config.from_yaml_file(args.config_file)

    loop = asyncio.get_event_loop()
    pool = loop.run_until_complete(db.create_pool(config.sql))
    loop.run_until_complete(run(pool, args.streamer_uuid))
