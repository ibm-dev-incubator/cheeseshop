# worker
# Takes one sc2 replay file and produces a json object
# produces two sets of time series, one set for each player, one time series
# for each unit type

# Rough structure:
# {
#   "map": "Echo LE(Void",
#   [
#      {
#        "name": "Neeb"
#        "army_supply": [
#          {
#             "name": "Seige Tank",
#             "color": "#4c0e73",
#             "data": [ { "x": 0, "y": 0 }, { "x": 1, "y" 0 } ... ]
#          },
#          ...
#        ],
#      },
#      {
#        "name": "MarineLord"
#        "army_supply": [
#          {
#             "name": "Seige Tank",
#             "color": "#4c0e73",
#             "data": [ { "x": 0, "y": 0 }, { "x": 1, "y" 0 } ... ]
#          },
#          ...
#        ],
#      }
#    ]
# }

import argparse
import hashlib
import json
import sys

import sc2reader
from sc2reader.engine.plugins import ContextLoader, GameHeartNormalizer

from cheeseshop.util import get_replay


def alive_at_this_time(unit, time, frames):
    if unit.died_at is None:
        unit.died_at = frames
    if time >= unit.finished_at and time <= unit.died_at:
        return True
    else:
        return False


# hand built
# duplicated in many places
army_units = ['Nuke',  # I guess
              'Marine',
              'Marauder',
              'Reaper',
              'Ghost',
              'BattleHellion',
              'Hellion',
              'Hellbat',
              'WidowMine',
              'SiegeTank',
              'Cyclone',
              'Thor',
              'Viking',
              'VikingFighter',
              'VikingAssault',
              'Medivac',
              'Liberator',
              'Raven',
              'Banshee',
              'Battlecruiser',
              'Nuke',  # I guess
              'Zealot',
              'Stalker',
              'Sentry',
              'Adept',
              'HighTemplar',
              'DarkTemplar',
              'Immortal',
              'Disruptor',
              'Colossus',
              'Archon',
              'Observer',
              'WarpPrism',
              'Phoenix',
              'VoidRay',
              'Oracle',
              'Tempest',
              'Carrier',
              'Zergling',
              'Roach',
              'Ravager',
              'Hydralisk',
              'SwarmHost',
              'Infestor',
              'Ultralisk',
              'Mutalisk',
              'Corruptor',
              'Viper',
              'Baneling',
              'BroodLord',
              'Overseer', ]


def parse_args(args):
    parser = argparse.ArgumentParser(
        description='Cheeseshop worker: supply_breakdown'
    )
    parser.add_argument('--sha1sum', type=str, help='Sha1sum of replay')
    return parser.parse_args(args)


def main():     # noqa: C901
    args = parse_args(sys.argv[1:])
    r = get_replay(args.sha1sum)
    replay = sc2reader.load_replay(
        r,
        engine=sc2reader.engine.GameEngine(plugins=[
            ContextLoader(),
            GameHeartNormalizer(),
        ])
    )

    data = {}
    data['map'] = replay.map_name
    data['players'] = []

    for player in replay.players:
        if not player.is_human:
            continue
        if player.is_observer:
            continue

        player_data = {}
        player_data['name'] = player.name

        unit_supplies = {}
        for unit_type in army_units:
            unit_supplies[unit_type] = []

        # All done in frames
        times = []
        game_end = replay.frames
        game_start = 0

        for current_frame in range(game_start, game_end, 160):
            times.append(current_frame)
            supply_per_unit = {}
            for unit_type in army_units:
                supply_per_unit[unit_type] = 0
            # Scan all units owned by player
            for unit in player.units:
                if unit.name not in army_units:
                    continue
                if alive_at_this_time(unit, current_frame, replay.frames):
                    supply_per_unit[unit.name] += unit.supply
            for unit_name, supply in supply_per_unit.items():
                unit_supplies[unit_name].append(supply)

        to_pop = []
        for key, value in unit_supplies.items():
            if sum(value) == 0:
                to_pop.append(key)

        for key in to_pop:
            unit_supplies.pop(key, None)

        # Create visualization-ready json object
        constructed_data = []
        for key, value in unit_supplies.items():
            obj = {}
            obj['name'] = key
            color = "#" + hashlib.sha224(bytes(key, 'utf-8')).hexdigest()[:6]
            obj['color'] = color
            xy_tuples = []
            for index, number in enumerate(value):
                point = {}
                point['x'] = times[index]
                point['y'] = number
                xy_tuples.append(point)
            obj['data'] = xy_tuples
            constructed_data.append(obj)

        player_data['army_supply'] = constructed_data
        data['players'].append(player_data)

    print(json.dumps(data))
