import uuid

import asynctest

from cheeseshop import config
from cheeseshop.tests import asyncfixtures


class TestCase(asynctest.TestCase, asyncfixtures.TestWithAsyncFixtures):
    def setUp(self):
        swift_config = config.SwiftConfig('swift_auth_url',
                                          'swift_project_id',
                                          'swift_user_id',
                                          'swift_password',
                                          'swift_region',
                                          'replays_container',
                                          'temp_url_key')
        sql_config = config.SqlConfig('cheeseshop',
                                      'cheeseshop-%s' % uuid.uuid4(),
                                      'localhost', 5432,
                                      'cheeseshop')
        self.config = config.Config('::', 8080, 'http://localhost',
                                    swift_config, sql_config)
