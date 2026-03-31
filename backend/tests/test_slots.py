import pytest
import asyncio
from src.slots.domain_task import Domain_Task
from src.slots.slot import Slot
from src.slots.slot_manager import Slot_Manager
from src.router.scan_request import ScanRequest

test_domain_slow="redhat.com"
test_domain_fast="intevation.de"

class TestSlotFunctionality():

    @pytest.mark.asyncio
    async def test_slot_functionality_and_capacity(self):
        scanRequestSlow = ScanRequest(domain=test_domain_slow, session_id="1")
        scanRequestSlow.skip_cache = True

        scanRequestFast = ScanRequest(domain=test_domain_fast, session_id="1")
        scanRequestFast.skip_cache = True

        # Limit available slots to one to test capacity
        Slot_Manager().slot_amount = 1
        Slot_Manager().slots = []
        for i in range(Slot_Manager().slot_amount):
            Slot_Manager().slots.append(Slot.create(i))

        assert Slot_Manager().find_first_available_slot() is not None

        taskUUID = Slot_Manager().start_domain_task(scanRequestSlow)

        assert Slot_Manager().get_slot_by_domain(test_domain_slow) is not None
        assert Slot_Manager().get_slot_by_domain(test_domain_fast) is None
        assert Slot_Manager().get_slot_by_task_id(taskUUID) is not None
        assert Slot_Manager().get_slot_by_task_id("-") is None
        assert Slot_Manager().find_first_available_slot() is None

        startingSameTaskAgainUUID = Slot_Manager().start_domain_task(scanRequestSlow)

        assert startingSameTaskAgainUUID == taskUUID

        secondTaskUUID = Slot_Manager().start_domain_task(scanRequestFast)

        assert secondTaskUUID == ""

    @pytest.mark.asyncio
    async def test_orphaned_tasks(self):
        # TODO
        return

    @pytest.mark.asyncio
    async def test_cached_tasks(self):
        # TODO
        return

    @pytest.mark.asyncio
    async def test_slot_task_status(self):
        # TODO
        return


