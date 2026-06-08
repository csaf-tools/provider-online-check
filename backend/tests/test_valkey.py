# SPDX-FileCopyrightText: 2026 German Federal Office for Information Security (BSI) <https://www.bsi.bund.de>
# Software-Engineering: 2026 Intevation GmbH <https://intevation.de>
#
# SPDX-License-Identifier: Apache-2.0

import pytest
from src.database.valkey import Valkey_Controller
from src.database.domain_task_data import Domain_Task_Data
from src.database.domain_name_hash_wrapper import Domain_Name_Hash_Wrapper

class TestValkeyController:
    """Tests for writing and reading from Valkey Controller"""

    def test_domain_blocking(self):
        domain = "test.com"

        Valkey_Controller().unblock_domain(domain) # Prevent flaky-ness
        assert Valkey_Controller().block_domain(domain) is True
        assert Valkey_Controller().block_domain(domain) is False

        assert Valkey_Controller().is_domain_in_domain_blocklist(domain) is True
        Valkey_Controller().unblock_domain(domain)
        assert Valkey_Controller().is_domain_in_domain_blocklist(domain) is False

    def test_client_blocking(self):
        session_id = "1"
        domain = "test.com"

        Valkey_Controller().unblock_session_id_for_domain(session_id, domain) # Prevent flaky-ness
        assert Valkey_Controller().block_session_id_for_domain(session_id, domain) is True
        assert Valkey_Controller().block_session_id_for_domain(session_id, domain) is False

        assert Valkey_Controller().is_session_id_in_client_blocklist(session_id, domain) is True
        Valkey_Controller().unblock_session_id_for_domain(session_id, domain)
        assert Valkey_Controller().is_session_id_in_client_blocklist(session_id, domain) is False

    def test_recording_task_results(self):
        domainWorking = "easterEgg.com"

        data = Domain_Task_Data.create(domainWorking)

        Valkey_Controller().record_domain_task(data)

        assert Valkey_Controller().get_domain_task_by_uuid(data.uuid) is not None
        assert Valkey_Controller().get_domain_task_by_domain_hash(Domain_Name_Hash_Wrapper().domain_hash(data.domain)) is not None

        assert Valkey_Controller().get_domain_task_by_uuid("-") is None
        assert Valkey_Controller().get_domain_task_by_domain_hash("-") is None
