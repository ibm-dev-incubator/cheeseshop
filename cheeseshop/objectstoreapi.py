class ReplayData(object):
    def __init__(self, uuid, container):
        self.uuid = uuid
        self.container = container

    async def set_data(self, swift_client, data):
        await swift_client.create_object(self.uuid, data, self.container)
