import json

from cheeseshop import dbapi


class SystemConfig(object):
    def __init__(self, conn):
        self._conn = conn

    async def last_migration(self):
        record = await dbapi.SystemConfig.get(self._conn, 'last-migration')
        return json.loads(record.value)

    async def set_last_migration(self, value):
        return await dbapi.SystemConfig.set(self._conn, 'last-migration',
                                            json.dumps(value))
