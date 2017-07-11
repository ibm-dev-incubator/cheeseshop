class FakeKeystoneSession(object):
    async def __aenter__(self):
        pass

    async def __aexit__(self, *args, **kwargs):
        pass


class FakeSwiftClient(object):
    async def __aenter__(self):
        pass

    async def __aexit(self, *args, **kwargs):
        pass
