# Reproducible performance measurements

`tools/perf-baseline.py` is a Python standard-library developer tool, not an
installed desktop component. Run it from a checkout. It never restarts the bar,
changes playback, or changes system settings. Use the same hardware, monitor
layout, power profile, background applications and durations before and after a
change. Keep the pointer away from the bar during idle measurements.

```sh
python3 tools/perf-baseline.py measure idle
python3 tools/perf-baseline.py measure panels --settle 30 --duration 60
python3 tools/perf-baseline.py measure music --assume-playing
python3 tools/perf-baseline.py measure startup --settle 0 --duration 2
python3 tools/perf-baseline.py compare /path/to/before.json /path/to/after.json
```

Each scenario accepts `--settle` (default 30 seconds), `--duration` (60), and
`--interval` (1). Music waits for Enter unless `--assume-playing` is supplied:
start music yourself first. Startup reads existing bar process start times and
ages relative to boot; it cannot establish first-frame or interactive readiness.
A fresh login, if desired, is manual. No session or service is restarted.

Panels repeats calendar, hardware, notifications, keyboard, media, theme picker,
then wallpaper picker, holding each for `--panel-seconds` (default 4). It closes
both panel surfaces between steps and on exit, including interruption or IPC
failure. It only presents panels, never selects choices or toggles devices.
It requires working `eitr-shell desktop-bar ipc call` access. Opening panels can
trigger their ordinary data reads. Settle occurs before this sequence starts;
the recorded action list identifies which steps fit within the sample duration.

JSON goes to `$XDG_STATE_HOME/eitr/perf/` (normally
`~/.local/state/eitr/perf/`), with private file permissions. `--output-dir` may
select another machine-local folder outside the checkout. Do not commit or
publish results: they contain hardware and process identifiers. The output
records the checkout revision separately from the installed Eitr version;
ensure the bar actually runs the revision being measured.

## What the numbers mean

- CPU seconds are deltas of user plus system time in `/proc/PID/stat`.
  `cpu_percent_one_core` is CPU seconds divided by actual elapsed time, times 100;
  it can exceed 100 for multithreaded processes. Groups are the desktop-bar
  Quickshell command line, `bar-data.py`, Elephant, Walker, Hyprland and hyprpaper.
  Other Quickshell shells are excluded. Group process counts expose absent groups.
- PSS and RSS are sampled from `smaps_rollup`, in KiB, with means across samples.
  An unreadable member makes that group's memory sample unavailable, not zero.
  Empty groups have zero memory. System readable sums include only readable
  processes, with coverage counts; RSS double-counts shared pages. System RAM
  used is `MemTotal - MemAvailable`. Access restrictions are not bypassed.
- Voluntary and nonvoluntary context-switch deltas come from each process's
  main-thread `/proc/PID/status`. These are a wakeup proxy, not hardware wakeups
  or a sum across every thread. System `ctxt` includes all tasks.
- Observed process launches are newly observed `(PID, start_ticks)` identities
  with parent PIDs, including unrelated system processes and the sampler's own
  helpers. They are a lower bound: processes born and exited between polls are
  missed, and processes exiting between polls lose their final CPU/switch deltas.
  PID reuse is distinguished by start time. System `/proc/stat` `processes` is a
  separate delta that counts task creation, including threads, not just processes.
- System CPU includes idle; `busy_cpu_seconds` excludes idle and iowait. Both
  are summed across CPUs. GPU samples are device-wide busy percent and watts
  from DRM sysfs where supported, plus optional `nvidia-smi`. Unavailable values
  are null or an empty device list. GPU data is not attributed to process groups.
  Every external reader has a three-second timeout; collection overhead and slow
  readers can extend the actual sample duration, which is recorded.

The compare table shows absolute differences in the stored units. Use matching
sample durations when comparing cumulative counters. It warns if configuration
or context differs. GPU device means appear in the table; time series remain in JSON for inspection. The tool
records CPU model/core count, RAM, GPU PCI description, kernel, power profile,
installed Eitr version and screen resolutions. Unavailable context is null or an
empty screen list; no hardware support is inferred from absent values.

## Separate instrumented frame runs

Frame tracing adds overhead and must be a separate opt-in run. On an isolated
test desktop, manually launch a test shell using the existing wrapper:

```sh
QSG_RENDER_TIMING=1 eitr-shell --repo /path/to/checkout desktop-bar
python3 tools/perf-baseline.py measure panels --instrumented
```

Keep the test shell's Qt diagnostic output locally and examine its render timing
messages separately. `--instrumented` labels the JSON; it does not enable tracing,
launch a shell, parse Qt's version-dependent logs, or claim per-surface frame
statistics. Never launch a second desktop bar over your normal session merely
for a baseline. Close the test shell manually afterward. Ordinary runs do not
collect frame timings or change the live bar environment.
