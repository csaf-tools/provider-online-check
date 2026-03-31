import pytest
import asyncio
import time
import logging
from src.csaf.csaf_checker import CSAF_Checker
from src.slots.domain_task import Domain_Task
from src.slots.domain_task import Domain_Task_Status
from src.database.domain_task_data import Domain_Task_Data

test_domain="woogle.de"
mock_session_id="1"

logger = logging.getLogger(__name__)

class TestWorkingDomainTask:
    """Tests for expected-case domain task"""

    @pytest.mark.asyncio
    async def test_start_and_stop(self):
        task = Domain_Task.create(test_domain, mock_session_id)
        task.debug_dont_save = True

        assert task.get_status() == Domain_Task_Status.INITIALIZED

        asyncio.create_task(task.run_checker())
        await asyncio.sleep(0.2)
        assert task.get_status() == Domain_Task_Status.RUNNING_CHECKER
        assert task.is_in_valid_state() == True

        task.stop_task()
        await asyncio.sleep(0.2)
        assert task.get_status() == Domain_Task_Status.INTERRUPTED
        assert task.is_in_valid_state() == False

    @pytest.mark.asyncio
    async def test_pause_and_unpause(self):
        task = Domain_Task.create(test_domain, mock_session_id)
        task.debug_dont_save = True

        asyncio.create_task(task.run_checker())
        await asyncio.sleep(0.2)

        task.pause_task()
        await asyncio.sleep(0.2)
        assert task.get_status() == Domain_Task_Status.PAUSED
        assert task.is_paused() == True

        task.unpause_task()
        await asyncio.sleep(0.2)
        assert task.get_status() != Domain_Task_Status.PAUSED
        assert task.is_paused() != True

        task.stop_task()
        await asyncio.sleep(0.2)
        assert task.get_status() == Domain_Task_Status.INTERRUPTED

    @pytest.mark.asyncio
    async def test_run_through(self):
        task = Domain_Task.create(test_domain, mock_session_id)
        task.debug_dont_save = True

        await asyncio.create_task(task.run_checker())

        assert task.get_status() == Domain_Task_Status.DONE



