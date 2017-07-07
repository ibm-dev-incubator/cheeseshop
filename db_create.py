# Script to create the tables needed in the db
# This assumes you've run 'create database <dbname>' somewhere
# This also requires a db_uri in the config file, which is the same data
# represented as a connection string instead of a dsn, sorry.
# Something to fix later

import argparse
import sys

from sqlalchemy import create_engine as sa_create_engine

from cheeseshop import dbapi
from cheeseshop import config as cs_config


def parse_args(args):
    parser = argparse.ArgumentParser(description='cheeseshop webapp.')
    parser.add_argument('config_file', type=str,
                        help='Path to config file')
    return parser.parse_args(args)

if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    config = cs_config.Config.from_yaml_file(args.config_file)
    dsn = config.db_uri

    engine = sa_create_engine(dsn)
    dbapi.metadata.create_all(engine)
    engine.dispose()

