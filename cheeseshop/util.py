# Common utilities
import os
import sys

def get_replay(sha1sum):
    """ Retrieve a replay given the sha1sum unique name of the
    replay file"""

    # TODO: make this use swift

    replay_dir = os.environ.get("REPLAY_DIR")
    if replay_dir is None:
        print("Error: please set the environment variable: REPLAY_DIR")
        sys.exit(1)
    replay_path = os.path.join(replay_dir, sha1sum + ".SC2Replay")
    return replay_path


def truthy(val):
    if type(val) == str:
        return val in ('True', 'true', 't', 'yes')
    return bool(val)
