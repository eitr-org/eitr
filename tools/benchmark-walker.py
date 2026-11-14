#!/usr/bin/env python3
"""Measure live Elephant queries without opening windows or activating actions."""
import argparse
import statistics
import subprocess
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repeats', type=int, default=15)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error('--repeats must be positive')
    cases = [('Main open', 'menus:main', ''), ('Main f', 'menus:main', 'f'),
             ('Main fi', 'menus:main', 'fi'), ('Main fir', 'menus:main', 'fir'),
             ('Apps open', 'menus:apps', '')]
    samples = {label: [] for label, _, _ in cases}
    for _ in range(args.repeats):
        for label, provider, query in cases:
            started = time.perf_counter()
            subprocess.run(['elephant', 'query', '--async=false', '--json',
                            f'{provider};{query};50'], check=True,
                           stdout=subprocess.DEVNULL, timeout=20)
            samples[label].append((time.perf_counter() - started) * 1000)
    print('CLI-inclusive wall milliseconds; no actions activated')
    for label, values in samples.items():
        ordered = sorted(values)
        percentile = ordered[min(len(ordered) - 1, int(len(ordered) * .95))]
        print(f'{label}: median={statistics.median(values):.2f} p95={percentile:.2f}')


if __name__ == '__main__':
    main()
