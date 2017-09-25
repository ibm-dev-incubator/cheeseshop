import _pickle as pickle
from collections import MutableSequence

from cheeseshop.demoparser import consts
from cheeseshop.demoparser.entities import BaseEntity
from cheeseshop.demoparser.entities import GameRules
from cheeseshop.demoparser.entities import Player
from cheeseshop.demoparser.entities import Team
from cheeseshop.demoparser.entities import Weapon


class EntityList(MutableSequence):

    def __init__(self, parser):
        self.parser = parser
        self._entities = [None] * (1 << consts.MAX_EDICT_BITS)
        self.class_map = {
            'DT_CSPlayer': Player,
            'DT_Team': Team,
            'DT_CSGameRules': GameRules,
            'DT_WeaponCSBase': Weapon
        }
        self._cache = {}

    def __getitem__(self, index):
        return self._entities.__getitem__(index)

    def __setitem__(self, index, value):
        self._entities.__setitem__(index, value)

    def __len__(self):
        return len(self._entities)

    def __delitem__(self, index):
        self._entities.__delitem__(index)

    def insert(self, index, value):
        self._entities.insert(index, value)

    def new_entity(self, index, class_id, serial):
        if self._entities[index]:
            self._entities[index] = None

        baseline = self.parser.instance_baselines[class_id]
        cls = BaseEntity

        if baseline:
            for table in self.class_map:
                if baseline.get(table):
                    cls = self.class_map[table]
                    break

        new_baseline = pickle.loads(pickle.dumps(baseline))
        assert baseline == new_baseline
        entity = cls(self.parser, index, class_id, serial, new_baseline)

        self._entities[index] = entity
        return entity

    def _get_by_class(self, cls):
        return [x for x in self._entities if isinstance(x, cls)]

    @property
    def players(self):
        return self._get_by_class(Player)

    @property
    def teams(self):
        return self._get_by_class(Team)


    def get_by_user_id(self, user_id):
        users = self.parser._table_by_name('userinfo')['entries']

        for idx, user in enumerate(users):
            if getattr(user['user_data'], 'user_id', None) == user_id:
                return self._entities[idx + 1]

    def get_by_handle(self, handle):
        ent = self._entities[handle & consts.NETWORKED_EHANDLE_ENT_ENTRY_MASK]
        if ent is None or ent.serial != (handle >> consts.MAX_EDICT_BITS):
            return

        return ent

    def get_one(self, table):
        if table in self._cache:
            return self._cache[table]

        for e in self._entities:
            if e and table in e.props:
                self._cache[table] = e
                return e
