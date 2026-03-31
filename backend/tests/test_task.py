import pytest
import asyncio
import time
import logging
from src.csaf.csaf_checker import CSAF_Checker
from src.database.database import Database_Manager
from src.slots.domain_task import Domain_Task
from src.slots.domain_task import Domain_Task_Status
from src.database.domain_task_data import Domain_Task_Data

test_domain_slow="redhat.com"
test_domain_fast="intevation.de"
mock_session_id="1"

logger = logging.getLogger(__name__)

def createTask(fast: bool) -> Domain_Task:
    if fast:
        domain = test_domain_fast
    else:
        domain = test_domain_slow
    task = Domain_Task.create(domain, mock_session_id)
    task.database_skip_cache = True
    task.get_data(True).enable_validator_cache = False

    return task

async def runTaskInBackground(task: Domain_Task):
    asyncio.create_task(task.run_checker())
    while task.get_csaf_checker() is None:
        await asyncio.sleep(0.1)

async def waitUntilLoopStepIncremented(task: Domain_Task):
    if task.get_csaf_checker() is None:
        return

    knownStepID = task.get_csaf_checker().get_loop_step()
    while (task.get_csaf_checker() is not None) and (knownStepID == task.get_csaf_checker().get_loop_step()):
        #logger.info(f"Status {task.get_status()} Loop Step {task.get_csaf_checker().get_loop_step()}")
        await asyncio.sleep(0.1)

class TestWorkingDomainTask:
    """Tests for domain tasks and csaf checker"""

    @pytest.mark.asyncio
    async def test_pause_and_unpause(self):
        task = createTask(False)

        await runTaskInBackground(task)

        task.pause_task()
        await waitUntilLoopStepIncremented(task)
        assert task.get_status() == Domain_Task_Status.PAUSED
        assert task.is_paused() == True

        task.unpause_task()
        await waitUntilLoopStepIncremented(task)
        assert task.get_status() != Domain_Task_Status.PAUSED
        assert task.is_paused() != True

        task.stop_task()
        await waitUntilLoopStepIncremented(task)
        assert task.get_status() == Domain_Task_Status.INTERRUPTED

    @pytest.mark.asyncio
    async def test_run_through(self):
        task = createTask(True)

        await asyncio.create_task(task.run_checker())

        assert task.get_status() == Domain_Task_Status.DONE

        # New signals should not be successful
        task.unpause_task()

        await waitUntilLoopStepIncremented(task)
        assert task.get_status() == Domain_Task_Status.DONE

    @pytest.mark.asyncio
    async def test_start_and_stop(self):
        task = createTask(False)

        assert task.get_status() == Domain_Task_Status.INITIALIZED

        await runTaskInBackground(task)

        assert task.get_status() == Domain_Task_Status.RUNNING_CHECKER
        assert task.is_in_valid_state() == True

        task.stop_task()
        await waitUntilLoopStepIncremented(task)

        assert task.get_status() == Domain_Task_Status.INTERRUPTED
        assert task.is_in_valid_state() == False

    @pytest.mark.asyncio
    async def test_pause_timout(self):
        task = createTask(False)

        await runTaskInBackground(task)

        task.get_csaf_checker()._max_wait_time = 1

        task.pause_task()
        await waitUntilLoopStepIncremented(task)
        while task.is_paused():
            await asyncio.sleep(0.1)

        assert task.get_status() == Domain_Task_Status.ERROR
        assert task.is_paused() != True

    @pytest.mark.asyncio
    async def test_restart_task(self):
        task = createTask(False)

        await runTaskInBackground(task)

        await waitUntilLoopStepIncremented(task)
        previousProcessPID = task.get_csaf_checker()._running_task_checker.pid

        # Check if PID unexpectedly changed
        await waitUntilLoopStepIncremented(task)
        assert task.get_csaf_checker()._running_task_checker.pid == previousProcessPID

        task.restart_task()

        # Check if PID changed as expected
        await waitUntilLoopStepIncremented(task)
        assert task.get_csaf_checker()._running_task_checker.pid != previousProcessPID

    @pytest.mark.asyncio
    async def test_signaling_missing_task(self):
        """ Tests if signals to a non existant task cause errors """
        task = createTask(False)

        # Propagate signals to task before starting csaf checker
        task.is_paused()
        task.is_orphaned()
        task.is_in_valid_state()
        task.pause_task()
        task.unpause_task()
        task.restart_task()
        task.stop_task()
        task.get_data(True)
        task.get_data(False)
        assert task.get_csaf_checker() is None

        task.status = Domain_Task_Status.ERROR
        assert task.is_in_valid_state() is False

    @pytest.mark.asyncio
    async def test_saving_to_database(self):
        task = createTask(True)
        task.database_skip_cache = False

        await asyncio.create_task(task.run_checker())

        assert task.get_status() == Domain_Task_Status.DONE

        data = Database_Manager().load_task_by_id(task.get_data(False).uuid)
        assert data is not None

        assert data.cache_is_outdated() is False
