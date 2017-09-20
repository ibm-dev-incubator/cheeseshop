from cheeseshop import systemconfig
from cheeseshop import dbapi
from cheeseshop.dbmigrations import (
    add_systemconfig,
    create_game_replay_schema,
    create_csgo_schema,
    create_sc2_csgo_game_records
)


# ONLY APPEND TO THIS LIST
# Migrations are run in order and we start off based on the last-migration
# property stored in SysemConfig.
migrations = [
    add_systemconfig,
    create_game_replay_schema,
    create_csgo_schema,
    create_sc2_csgo_game_records
]


async def run_migrations(conn):
    sc = systemconfig.SystemConfig(conn)
    create_initial_schema = False
    last_migration = None

    try:
        last_migration = await sc.last_migration()
    except (dbapi.SchemaError, dbapi.NotFoundError):
        create_initial_schema = True

    if create_initial_schema:
        await dbapi.SystemConfig.create_schema(conn)

    start_migrating = False
    if last_migration is None:
        start_migrating = True
    for migration in migrations:
        cur_name = migration.__name__.rsplit('.', 1)[1]
        if start_migrating is False:
            # Check if were up to last_migration and if so start migrating
            if last_migration == cur_name:
                start_migrating = True
                continue
        else:
            await migration.run(conn)
            await sc.set_last_migration(cur_name)
