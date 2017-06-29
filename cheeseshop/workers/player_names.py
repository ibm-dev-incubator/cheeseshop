# worker
# Takes one sc2 replay file and produces some text (later thrown in a db)
# produces the names and races of the players

# This mostly exists as a template that new workers can be cargo'd from

import argparse
import sys
import sc2reader
from sc2reader.engine.plugins import ContextLoader, GameHeartNormalizer

from cheeseshop.util import get_replay

def parse_args(args):
    parser = argparse.ArgumentParser(description='Cheeseshop worker: player_names')
    parser.add_argument('--sha1sum', type=str, help='Sha1sum of replay')
    return parser.parse_args(args)

def main():
    args = parse_args(sys.argv[1:])
    print("Accessing replay, id: {0}".format(args.sha1sum))
    r = get_replay(args.sha1sum)
    replay = sc2reader.load_replay(
        r,
        engine=sc2reader.engine.GameEngine(plugins=[
            ContextLoader(),
            GameHeartNormalizer(),
        ])
    )
    for p in replay.players:
        print(p)
