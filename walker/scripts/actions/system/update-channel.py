#!/usr/bin/env python3
"""Switch the Eitr update channel; Walker's Update Channel menu runs it in a terminal.

  update-channel.py set stable|testing
"""
import eitr_bootstrap
from eitr_i18n import tr
from pathlib import Path
import subprocess
import sys

HELPER = "/usr/lib/eitr/eitr-system"

EXPLANATION = {
    "testing": "Testing gets new Eitr builds as soon as they are published, before everyone else, so you can "
               "try changes early. They are less tested; a snapshot still protects every System Update.",
    "stable": "Stable gets Eitr builds once they have been tried on the testing channel.",
}


def main(argv):
    if len(argv) != 2 or argv[0] != "set" or argv[1] not in EXPLANATION:
        sys.exit(__doc__)
    if not Path(HELPER).is_file():
        raise RuntimeError(tr('The root-owned Eitr helper is not installed; update the eitr-desktop package.'))
    channel = argv[1]
    print(tr('Switching to the {channel} channel.\n\n{explanation}\n', channel=f'{channel}', explanation=f'{EXPLANATION[channel]}'))
    subprocess.run(["sudo", HELPER, "channel-set", channel], check=True)
    print(tr('\nUpdate channel: {channel}. The next System Update uses it.', channel=f'{channel}'))


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        sys.exit(str(error))
    except (EOFError, KeyboardInterrupt):
        sys.exit("Nothing was changed.")
