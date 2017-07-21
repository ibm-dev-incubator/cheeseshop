class GameApi(object):
    def __init__(self, config, sql_pool):
        self.config = config
        self.sql_pool = sql_pool
