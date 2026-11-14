"""Machine-local login milestones, on Linux's suspend-aware monotonic boot clock."""
import fcntl
import json
import os
from pathlib import Path
import time


def location():
    return Path(os.environ.get('XDG_STATE_HOME', Path.home() / '.local/state')) / 'eitr/login-timing.jsonl'


def mark(event):
    try:
        with location().open('a') as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            json.dump(dict(event=event, monotonic=time.clock_gettime(time.CLOCK_BOOTTIME),
                           wall=time.time()), handle)
            handle.write('\n')
    except OSError:
        pass


def main():
    rows = [json.loads(line) for line in location().read_text().splitlines()]
    rows.sort(key=lambda row: row['monotonic'])
    for row in rows:
        print(f"{row['monotonic'] - rows[0]['monotonic']:7.3f}s  {row['event']}")


if __name__ == '__main__':
    main()
