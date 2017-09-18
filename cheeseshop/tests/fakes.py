import collections


swift_storage = None


def set_swift_object(name, data, container):
    global swift_storage
    swift_storage[container][name] = data


def get_swift_object(name, container):
    global swift_storage
    return swift_storage[container][name]


class FakeKeystoneSession(object):
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        pass

    async def __aexit__(self, *args, **kwargs):
        pass


class FakeSwiftClient(object):
    def __init__(self, keystone_session, region_id, interface='public',
                 temp_url_key=None):
        global swift_storage
        if swift_storage is None:
            swift_storage = collections.defaultdict(dict)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args, **kwargs):
        pass

    async def create_object(self, name, data, container):
        set_swift_object(name, data, container)

    async def get_object(self, name, container):
        return get_swift_object(name, container)

    async def create_tempurl(self, name, container):
        return 'http://some-swift.com/tempurl-unique'
