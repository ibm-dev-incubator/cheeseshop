import uuid

import asynctest

from cheeseshop import config
from cheeseshop.tests import asyncfixtures


class TestCase(asynctest.TestCase, asyncfixtures.TestWithAsyncFixtures):
    def setUp(self):
        swift_config = config.SwiftConfig(None, None, None, None, None)
        sql_config = config.SqlConfig('cheeseshop',
                                      'cheeseshop-%s' % uuid.uuid4(),
                                      'localhost', 5432,
                                      'cheeseshop')
        self.config = config.Config('::', 8080, swift_config, sql_config)
