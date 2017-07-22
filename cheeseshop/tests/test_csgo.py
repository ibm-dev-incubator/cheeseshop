from cheeseshop.games import csgo
from cheeseshop.tests import base


class TestMapState(base.TestCase):
    async def test_from_gsi_event(self):
        state = csgo.MapState.from_gsi_event({
            'map': {
                'phase': 'live',
                'team_t': {
                    'name': 't team'
                },
                'team_ct': {
                    'name': 'ct team'
                },
                'name': 'map name'
            }
        })
        self.assertEqual(state.phase, 'live')
        self.assertEqual(state.name, 'map name')
        self.assertEqual(state.team_t, 't team')
        self.assertEqual(state.team_ct, 'ct team')
