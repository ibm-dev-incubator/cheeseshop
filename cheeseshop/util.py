# Common utilities
import os

def get_replay(sha1sum):
    """ Retrieve a replay given the sha1sum unique name of the
    replay file"""

    # TODO: make this use swift

    replay_dir = os.environ.get("REPLAY_DIR")
    replay_path = os.path.join(replay_dir, sha1sum + ".SC2Replay")
    return replay_path

