class ReplayData(object):
    def __init__(self, uuid):
        self.uuid = uuid

    async def write(self, swift_client, data):
        import pdb;pdb.set_trace()
        print('a')
        
