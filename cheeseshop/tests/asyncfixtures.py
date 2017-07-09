import fixtures
from fixtures.fixture import gather_details


class TestWithAsyncFixtures:
    async def useAsyncFixture(self, fixture):
	# Code modified from fixtures.testcase
        use_details = (
            gather_details is not None and
            getattr(self, "addDetail", None) is not None)
        try:
            await fixture.setUp()
        except:
            if use_details:
                # Capture the details now, in case the fixture goes away.
                gather_details(fixture.getDetails(), self.getDetails())
            raise
        else:
            self.addCleanup(fixture.cleanUp)
            if use_details:
                # Capture the details from the fixture during test teardown;
                # this will evaluate the details before tearing down the
                # fixture.
                self.addCleanup(gather_details, fixture, self)
            return fixture


class AsyncFixture(fixtures.Fixture):
    async def setUp(self):
        super(AsyncFixture, self).setUp()
        await self._setUp()

    async def _setUp(self):
        pass

    async def cleanUp(self):
        super(AsyncFixture, self).cleanUp()
        # TODO(greghaynes): Add call async cleanups
