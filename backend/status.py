#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 German Federal Office for Information Security (BSI) <https://www.bsi.bund.de>
# Software-Engineering: 2026 Intevation GmbH <https://intevation.de>
#
# SPDX-License-Identifier: Apache-2.0
#
# Status tool for sysadmins
# Run from inside the backend container:
#
#   docker compose exec backend ./status.py

import json
import os
import sys
from datetime import datetime, timezone
from typing import Optional

import httpx2
import valkey

# currently all of them are static
BACKEND_URL = "http://localhost:8000"
VALKEY_HOST = "valkey"
VALKEY_PORT = 6379

RECORDED_DOMAIN_TASK_BY_UUID = "domain-task-id-to-domain:"  # keep in sync with src/database/valkey.py
CACHE_LIFETIME = int(os.environ.get("CACHE_TIMEOUT_SECONDS", "604800"))


def fmt_ts(ts: Optional[int]) -> str:
    if not ts:
        return "-"
    # remove trailing +00:00, is always UTC anyway
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()[:-6]


def fmt_duration(seconds: int) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes:02d}m {seconds:02d}s"
    if minutes:
        return f"{minutes}m {seconds:02d}s"
    return f"{seconds}s"


def section(title: str):
    print(f"\n=== {title} ===")


def print_health(client: httpx2.Client):
    section("System Health")
    try:
        request = client.get(f"{BACKEND_URL}/api/health", timeout=5)
        health = request.json()
    except Exception as exc:
        print(f"  Could not reach backend: {exc}")
        return

    print(f"Status:     {health.get('status', '?')}")
    print(f"Free slots: {health.get('free_slots', '?')} / {health.get('total_slots', '?')}")

    for key in ("csaf_checker_available", "valkey_available",
                "validator_available"):
        print(f"{key}: {health.get(key)}")

    if health.get("errors"):
        for error in health["errors"]:
            print(f"  ! {error}")


def print_running(client: httpx2.Client):
    section("Running Scans")
    try:
        request = client.get(f"{BACKEND_URL}/api/admin/status", timeout=5)
        data = request.json()
    except Exception as exc:
        print(f"  Could not reach backend: {exc}")
        return

    slots = data.get("slots", [])
    active_slots = [slot for slot in slots if not slot["available"]]
    idle_count = len(slots) - len(active_slots)

    if active_slots:
        now = int(datetime.now(tz=timezone.utc).timestamp())
        print(f"{'Slot':>4}  {'Domain':<30}  {'Status':<20}  {'Files':>5}  {'Running':>10}  Started (UTC)")
        for slot in active_slots:
            start = slot.get('start_time') or 0
            print(
                f"{slot['id']:>4}  {slot.get('domain') or '':<30}  "
                f"{slot.get('status') or '':<20}  "
                f"{slot.get('files_checked') or 0:>5}  "
                f"{fmt_duration(now - start) if start else '-':>10}  "
                f"{fmt_ts(start)}"
            )
    print(f"{idle_count} slot(s) idle")


def print_cached():
    section("Cached Check results")
    try:
        cache = valkey.Valkey(host=VALKEY_HOST, port=VALKEY_PORT, db=0, protocol=3)
        keys = cache.keys(RECORDED_DOMAIN_TASK_BY_UUID + "*")
    except Exception as exc:
        print(f"  Could not reach cache: {exc}")
        return

    tasks = []
    for key in keys:
        raw = cache.get(key)
        if not raw:
            continue
        try:
            t = json.loads(raw)
            tasks.append(t)
        except Exception as exc:
            print(f"  Error decoding key {key!r}: {exc}")
            continue

    tasks.sort(key=lambda t: t.get("start_time", 0), reverse=True)

    if not tasks:
        print("  No cached scans.")
        return

    print(
        f"{'Domain':<30}  {'Result':>6}  {'Role':<25}  {'Duration':>8}  "
        f"{'Started (UTC)':<19}  {'Expires (UTC)':<19}"
    )
    for t in tasks:
        domain = t.get("domain", "?")
        start = t.get("start_time")
        end = t.get("end_time")
        duration = fmt_duration(end - start) if end and start else 'unknown'
        expires = fmt_ts(end + CACHE_LIFETIME) if end else 'unknown'

        passed = None
        role = None
        result_json = t.get("csaf_checker_output_result", "")
        if result_json:
            try:
                result = json.loads(result_json)
                domains = result.get("domains", [])
                if domains:
                    passed = domains[0].get("passed")
                    role = domains[0].get("role")
            except Exception as exc:
                print(f"  Error decoding result JSON of domain {domain!r}: {exc}")
                pass

        result_str = "PASS" if passed is True else "FAIL"
        role_str = role or "-"

        print(
            f"{domain:<30}  {result_str:>6}  {role_str:<25}  {duration:>8}  "
            f"{fmt_ts(start):<19}  {expires:<19}"
        )


def main():
    with httpx2.Client() as client:
        print_health(client)
        print_running(client)
    print_cached()
    print()


if __name__ == "__main__":
    main()
