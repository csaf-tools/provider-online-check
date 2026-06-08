# SPDX-FileCopyrightText: 2026 German Federal Office for Information Security (BSI) <https://www.bsi.bund.de>
# Software-Engineering: 2026 Intevation GmbH <https://intevation.de>
#
# SPDX-License-Identifier: Apache-2.0

from sys import getsizeof
from unittest.mock import patch

import pytest

import src.database.domain_task_data as dtd
from src.database.domain_task_data import (
    Domain_Task_Data,
    RUNTIME_LOG_MAX_BYTES,
    RUNTIME_LOG_TRUNCATE_LINES,
    RUNTIME_LOG_TRUNCATE_MESSAGE,
)


def make_data(prefill_lines: int = 0) -> Domain_Task_Data:
    data = Domain_Task_Data.create("example.com")
    for i in range(prefill_lines):
        data.csaf_checker_output_runtime_log.append(f"line {i}")
    return data


class TestLogTruncation:

    def test_no_truncation_below_limit(self):
        data = make_data(prefill_lines=10)
        assert RUNTIME_LOG_TRUNCATE_MESSAGE not in data.csaf_checker_output_runtime_log
        assert len(data.csaf_checker_output_runtime_log) == 10

    def test_truncation_replaces_exactly_truncate_lines_entries(self):
        n = RUNTIME_LOG_TRUNCATE_LINES + 10
        data = make_data(prefill_lines=n)
        # subtract 1 so the threshold is already exceeded after the append
        max_bytes = getsizeof(data.csaf_checker_output_runtime_log) - 1
        with patch.object(dtd, "RUNTIME_LOG_MAX_BYTES", max_bytes):
            data.append_runtime_log("new")
        assert data.csaf_checker_output_runtime_log[0] == RUNTIME_LOG_TRUNCATE_MESSAGE
        # RUNTIME_LOG_TRUNCATE_LINES entries replaced by 1 message + new line appended
        assert len(data.csaf_checker_output_runtime_log) == n - RUNTIME_LOG_TRUNCATE_LINES + 1 + 1
