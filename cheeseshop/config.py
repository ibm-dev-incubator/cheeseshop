import yaml

class SwiftConfig(object):
    def __init__(self, auth_url, project_id, user_id, password, region):
        self.auth_url = auth_url
        self.project_id = project_id
        self.user_id = user_id
        self.password = password
        self.region = region


class Config(object):
    @staticmethod
    def from_yaml_file(path):
        with open(path, 'r') as fh:
            raw_config = yaml.load(fh)
        swift_config = SwiftConfig(**raw_config['swift'])
        return Config(raw_config['host'], raw_config['port'], swift_config)

    def __init__(self, host, port, swift):
        self.host = host
        self.port = int(port)
        self.swift = swift
