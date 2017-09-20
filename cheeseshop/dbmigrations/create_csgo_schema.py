from cheeseshop import dbapi


async def run(conn):
    await dbapi.CsGoHltvEventType.create_schema(conn)
    await dbapi.CsGoHltvEvent.create_schema(conn)
    await dbapi.CsGoSteamId.create_schema(conn)
    await dbapi.CsGoDeathEvent.create_schema(conn)
    await dbapi.CsGoStreamer.create_schema(conn)
    await dbapi.CsGoGsiEvent.create_schema(conn)
    await dbapi.CsGoMap.create_schema(conn)
    await dbapi.CsGoEventMapRelation.create_schema(conn)
