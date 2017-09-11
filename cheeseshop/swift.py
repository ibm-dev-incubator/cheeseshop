import aiohttp

class KeystoneCatalogEndpoint(object):
    def __init__(self, id, interface, region, region_id, url):
        self.id = id
        self.interface = interface
        self.region = region
        self.region_id = region_id
        self.url = url


class KeystoneCatalogService(object):
    def __init__(self, id, name, service_type, endpoints):
        self.id = id
        self.name = name
        self.service_type = service_type
        self.endpoints = endpoints

    @classmethod
    def from_raw_service_entry(self, service_entry):
        endpoints = map(lambda x: KeystoneCatalogEndpoint(**x),
                        service_entry['endpoints'])
        id = service_entry['id']
        service_type = service_entry['type']
        name = service_entry['name']
        return KeystoneCatalogService(id, name, service_type, endpoints)

    def get_endpoints(self, interface=None, region=None, region_id=None):
        endpoints = self.endpoints
        if interface is not None:
            endpoints = filter(lambda x: x.interface == interface, endpoints)
        if region is not None:
            endpoints = filter(lambda x: x.region == region, endpoints)
        if region_id is not None:
            endpoints = filter(lambda x: x.region_id == region_id, endpoints)
        return endpoints


class KeystoneCatalog(object):
    @classmethod
    def from_raw_catalog(self, raw_catalog):
        services = map(
            lambda x: KeystoneCatalogService.from_raw_service_entry(x),
            raw_catalog
        )
        return KeystoneCatalog(services)

    def __init__(self, services):
        self.services = services

    def get_services(self, service_type=None):
        services = self.services
        if service_type is not None:
            services = filter(lambda x: x.service_type == service_type,
                              services)
        return services


class KeystoneToken(object):
    def __init__(self, token_id, expires_at):
        self.token_id = token_id
        self.expires_at = expires_at


class KeystoneSession(object):
    def __init__(self, auth_url, project_id, user_id, password):
        self.auth_url = auth_url
        self.project_id = project_id
        self.user_id = user_id
        self.password = password
        self._latest_token = None
        self.catalog = []

    async def __aenter__(self):
        token_uri = '%s/v3/auth/tokens' % self.auth_url
        async with aiohttp.ClientSession() as client:
            async with client.post(token_uri, json=self.get_req_obj()) as req:
                assert req.status == 201
                # TODO(greghaynes): Set expires time
                self._latest_token = KeystoneToken(
                    req.headers['X-Subject-Token'],
                    None
                )
                token_resp = await req.json()
                self.catalog = KeystoneCatalog.from_raw_catalog(
                    token_resp['token']['catalog']
                )
        return self

    async def __aexit__(self, *args):
        pass

    @property
    def token(self):
        return self._latest_token

    def get_req_obj(self):
        return {
            "auth": {
                "identity": {
                    "methods": [
                        "password"
                    ],
                    "password": {
                        "user": {
                            "id": self.user_id,
                            "password": self.password
                        }
                    }
                },
                "scope": {
                    "project": {
                        "id": self.project_id
                    }
                }
            }
        }


class SwiftClient(object):
    def __init__(self, keystone_session, region_id, interface='public',
                 container=None):
        self._keystone_session = keystone_session
        self.region_id = region_id
        self.interface = interface
        self.container = container
        self.service = None

    async def __aenter__(self):
        catalog = self._keystone_session.catalog
        object_services = list(catalog.get_services('object-store'))
        assert len(object_services) == 1
        self.service = object_services[0]

        endpoints = list(self.service.get_endpoints(region_id=self.region_id,
                                                    interface=self.interface))
        assert len(endpoints) == 1
        self.endpoint = endpoints[0]
        return self

    async def __aexit__(self, *args):
        pass

    async def create_object(self, name, data, container=None):
        assert container is not None or self.container is not None
        container = container or self.container
        put_uri = '%s/%s/%s' % (self.endpoint.url, container, name)
        headers = {'X-Auth-Token': self._keystone_session.token.token_id}
        async with aiohttp.ClientSession() as client:
            async with client.put(put_uri, data=data, headers=headers) as req:
                txt = await req.text()
                assert req.status == 201

    async def create_tempurl(self, name, container=None):
        assert container is not None or self.container is not None
        container = container or self.container

        # TODO:greghaynes Implement this
