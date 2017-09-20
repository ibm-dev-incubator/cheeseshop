import yaml


class SwiftConfig(object):
    def __init__(self, auth_url, project_id, user_id, password, region,
                 replays_container, temp_url_key):
        self.auth_url = auth_url
        self.project_id = project_id
        self.user_id = user_id
        self.password = password
        self.region = region
        self.replays_container = replays_container
        self.temp_url_key = temp_url_key.encode()


class SqlConfig(object):
    def __init__(self, user, database, host, port, password,
                 minsize=1, maxsize=10):
        self.user = user
        self.database = database
        self.host = host
        self.port = port
        self.password = password
        self.maxsize = maxsize
        self.minsize = minsize


class Config(object):
    @staticmethod
    def from_yaml_file(path):
        with open(path, 'r') as fh:
            raw_config = yaml.load(fh)
        swift_config = SwiftConfig(**raw_config['swift'])
        sql_config = SqlConfig(**raw_config['sql'])
        return Config(raw_config['host'], raw_config['port'],
                      raw_config['base_uri'], swift_config, sql_config)

    def __init__(self, host, port, base_uri, swift, sql):
        self.host = host
        self.port = int(port)
        self.base_uri = base_uri
        self.swift = swift
        self.sql = sql
