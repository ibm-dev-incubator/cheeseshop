import collections
from hashlib import sha1
from cheeseshop.swift import SwiftClient


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


class FakeEndpoint(object):
    def __init__(self, url):
        self.url = url


class FakeSwiftClient(SwiftClient):
    def __init__(self, keystone_session, region_id, interface='public',
                 temp_url_key=None):
        global swift_storage
        if swift_storage is None:
            swift_storage = collections.defaultdict(dict)
        self.endpoint = FakeEndpoint("https://swift.herpderp.com/"
                                     "v1/AUTH_herpthederp3000")
        self.temp_url_key = temp_url_key

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args, **kwargs):
        pass

    async def create_object(self, name, data, container):
        set_swift_object(name, data, container)

    async def get_object(self, name, container):
        return get_swift_object(name, container)


class FakeHmac(object):
    def __init__(self, key, hmac_body, digest=sha1):
        self.key = key
        self.hmac_body = hmac_body
        self.digest = digest

    def hexdigest(self):
        return "DAEDBEFFCAFE"
