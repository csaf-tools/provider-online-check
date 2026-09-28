#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 German Federal Office for Information Security (BSI) <https://www.bsi.bund.de>
# Software-Engineering: 2026 Intevation GmbH <https://intevation.de>
#
# SPDX-License-Identifier: Apache-2.0
#
# Rudimentary usage statistics from the Apache access log.
# Run on the server running the Apache reverse-proxy:
#
#   ./contrib/analyze_access_log.py /var/log/apache2/other_vhosts_access.log*
#
# Parses both plain "combined" and Debian's "vhost_combined" format,
# with or without an appended response time %D.
# Rotated/compressed logs (access.log.N, access.log.N.gz) are analysed automatically too.
#
# Parts of the Referer header are read too: domain and observe_rerun

import argparse
import gzip
import re
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime
from typing import Optional
from urllib.parse import parse_qs, urlsplit

SCAN_START_PATH = "/api/scan/start"
BLOCKED_PATH = "/blocked.html"

# unknown paths will be ignored
KNOWN_PATHS = {
    "/",
    SCAN_START_PATH,
    "/api/information",
    "/api/health",
    "/api/docs",
    "/api/openapi.json",
    BLOCKED_PATH,
}

# %v:%p %h %l %u %t "%r" %>s %O "%{Referer}i" "%{User-Agent}i" [%D]
LOG_LINE_RE = re.compile(
    r"^(?:(?P<vhost>\S+):\d+\s+)?"
    r"\S+\s+\S+\s+\S+\s+"
    r"\[(?P<time>[^\]]+)\]\s+"
    r'"(?P<method>\S+)\s+(?P<path>\S+)\s+\S+"\s+'
    r"(?P<status>\d{3})\s+"
    r"(?P<size>\S+)\s+"
    r'"(?P<referer>[^"]*)"\s+'
    r'"(?P<useragent>[^"]*)"'
    r"(?:\s+(?P<response_time>\d+))?\s*$"
)


def open_log_file(path: str):
    if path.endswith(".gz"):
        return gzip.open(path, "rt", errors="replace")
    return open(path, "rt", errors="replace")


def parse_referer_params(referer: str) -> dict:
    if not referer:
        return {}
    query = urlsplit(referer).query
    if not query:
        return {}
    return {k: v[0] for k, v in parse_qs(query).items()}


def status_bucket(status: str) -> str:
    return f"{status[0]}xx" if status and status[0].isdigit() else "?"


def fmt_ts(timestamp: str) -> str:
    # Apache formats %t time in absurd formatting: "28/Sep/2026:14:35:39 +0200"
    try:
        return datetime.strptime(timestamp, "%d/%b/%Y:%H:%M:%S %z").isoformat()
    except ValueError:
        return timestamp


def section(title: str):
    print(f"\n=== {title} ===")


def analyze(paths: list, vhost_filter: Optional[str]) -> None:
    total_lines = 0
    unparsed = 0
    first_ts = None
    last_ts = None

    path_status = defaultdict(Counter)
    forbidden_count = 0

    scan_total = 0
    scan_rerun = 0
    scan_domains = Counter()

    response_times = defaultdict(list)
    has_response_time = False

    vhost_hits = Counter()
    saw_vhost = False

    for path in paths:
        try:
            fh = open_log_file(path)
        except OSError as exc:
            print(f"Could not open {path}: {exc}", file=sys.stderr)
            continue

        with fh:
            for line in fh:
                line = line.rstrip("\n")
                if not line:
                    continue
                total_lines += 1

                match = LOG_LINE_RE.match(line)
                if not match:
                    unparsed += 1
                    continue

                vhost = match.group("vhost")
                if vhost:
                    saw_vhost = True
                    vhost_hits[vhost] += 1
                    if vhost_filter and vhost != vhost_filter:
                        continue

                request_path = match.group("path")
                if request_path not in KNOWN_PATHS:
                    continue

                status = match.group("status")
                referer = match.group("referer")
                response_time = match.group("response_time")

                params = {}
                if request_path == SCAN_START_PATH:
                    params = parse_referer_params(referer)

                timestamp = match.group("time")
                first_ts = first_ts or timestamp
                last_ts = timestamp

                path_status[request_path][status_bucket(status)] += 1

                if status == "403":
                    forbidden_count += 1

                if request_path == SCAN_START_PATH:
                    scan_total += 1
                    if params.get("observe_rerun") == "true":
                        scan_rerun += 1
                    if "domain" in params:
                        scan_domains[params["domain"]] += 1

                if response_time is not None:
                    has_response_time = True
                    response_times[request_path].append(int(response_time))

    section("Summary")
    print(f"Lines parsed:   {total_lines - unparsed} / {total_lines}")
    if unparsed:
        print(f"  ({unparsed} line(s) did not match the expected log format)")
    if first_ts and last_ts:
        print(f"Time range:     {fmt_ts(first_ts)} .. {fmt_ts(last_ts)}")

    section("Requests by path")
    print(f"{'Path':<30}  {'Total':>7}  {'2xx':>6}  {'3xx':>6}  {'4xx':>6}  {'5xx':>6}")
    for request_path, counts in sorted(
        path_status.items(), key=lambda kv: -sum(kv[1].values())
    ):
        total = sum(counts.values())
        print(
            f"{request_path:<30}  {total:>7}  "
            f"{counts.get('2xx', 0):>6}  {counts.get('3xx', 0):>6}  "
            f"{counts.get('4xx', 0):>6}  {counts.get('5xx', 0):>6}"
        )

    section("Scan requests")
    if scan_total:
        print(f"Total:          {scan_total}")
        # just a very rough differentiation
        print(f"observe_rerun=true:   {scan_rerun}")
        print(f"observe_rerun=false:  {scan_total - scan_rerun}")

        if scan_domains:
            print("\nScan targets:")
            for domain, count in scan_domains.most_common():
                print(f"  {count:>5}  {domain}")
    else:
        print("  No scan requests found.")

    section("Blocked requests")
    print(f"403 responses: {forbidden_count}")

    if has_response_time:
        section("Response times (ms)")
        print(f"{'Path':<30}  {'Min':>8}  {'Median':>8}  {'Max':>8}")
        for request_path, times in sorted(
            response_times.items(), key=lambda kv: -len(kv[1])
        ):
            ms = [t / 1000 for t in times]
            print(
                f"{request_path:<30}  {min(ms):>8.1f}  {statistics.median(ms):>8.1f}  {max(ms):>8.1f}"
            )

    # no --vhost given: show the breakdown, since all vhosts were considered
    if saw_vhost and not vhost_filter:
        section("By vhost")
        for vhost, count in vhost_hits.most_common():
            print(f"{count:>7}  {vhost}")

    print()


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("logfile", nargs="+", help="access log file(s), plain or .gz")
    parser.add_argument("--vhost", help="only consider requests to this vhost domain")
    args = parser.parse_args()

    analyze(args.logfile, args.vhost)


if __name__ == "__main__":
    main()
