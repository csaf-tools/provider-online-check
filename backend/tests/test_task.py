import pytest
import asyncio
import time
import logging
from src.csaf.csaf_checker import CSAF_Checker
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
    task.debug_dont_save = True
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
        logger.info(f"Status {task.get_status()} Loop Step {task.get_csaf_checker().get_loop_step()}")
        await asyncio.sleep(0.1)

class TestWorkingDomainTask:
    """Tests for expected-case domain task"""

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
    async def test_pause_timout(self):
        task = createTask(False)

        await runTaskInBackground(task)

        task.get_data(True)._wait_time_interval = 1

        task.pause_task()
        await waitUntilLoopStepIncremented(task)

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

