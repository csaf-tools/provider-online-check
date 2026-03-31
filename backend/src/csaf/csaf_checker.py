# Interface to call, communicate with and save results of csaf checker

# Involved in: 7, 8, 9
import asyncio
import logging
import os
import signal
from pathlib import Path
from typing import Annotated, Optional

from pydantic import BaseModel, Field

from ..database.domain_task_data import Domain_Task_Data

logger = logging.getLogger(__name__)

CSAF_BINARY_PATH = "/app/bin/csaf-binary/bin-linux-amd64/"
CSAF_CHECKER_BINARY = "csaf_checker"
CACHE_PATH_VALIDATOR = "/app/store/validator/cache/"


class CSAF_Checker(BaseModel):
    _loop_step: Annotated[
        int,
        Field(
            description="Current loop iteration step. Increments each time the run loop is reiterated"
        )
    ] = 0

    _signal_paused: Annotated[
        bool,
        Field(
            description="Setting this to true, causes the running task to be paused in the next run-iteration. Likewise, setting it to false causes the task to unpause"
        ),
    ] = False
    _signal_stop: Annotated[
        bool,
        Field(
            description="Setting this to true, causes the running task to be stopped in the next run-iteration"
        ),
    ] = False
    _signal_restart: Annotated[
        bool,
        Field(
            description="Setting this to true, causes the running task to be restarted in the next run-iteration"
        ),
    ] = False

    _running_task_checker: Annotated[
        Optional[asyncio.subprocess.Process],
        Field(description="Asynchronious task running csaf checker"),
    ] = None

    _max_wait_time: Annotated[
        int,
        Field(
            description="Time in seconds a task is allowed to be in a paused state before being forcefully stopped"
        ),
    ] = int(os.environ.get("TASK_PAUSE_TIME_MAX_BEFORE_RESET", "100"))

    _wait_time_interval: Annotated[
        float,
        Field(description="Interval used for task sleeping while the task is paused"),
    ] = float(os.environ.get("TASK_PAUSE_TIME_INTERVAL", "0.2"))

    def pause(self):
        self._signal_paused = True

    def unpause(self):
        self._signal_paused = False

    def stop(self):
        self._signal_stop = True

    def restart(self):
        self._signal_restart = True

    def get_loop_step(self) -> int:
        return self._loop_step

    def __csaf_checker_path(self) -> str:
        return os.path.join(CSAF_BINARY_PATH, CSAF_CHECKER_BINARY)

    async def __start_asyncio_task(self, data: Domain_Task_Data):
        # FIXME
        # Handle non-null running task
        await self.__terminate_asyncio_task()

        # Write args
        args = ["--verbose", data.domain]

        if data.enable_validator:
            args.append("--validator=http://validator:8082")

            if data.enable_validator_cache:
                # Create cache folder if it doesnt exist yet
                cache_path = Path(CACHE_PATH_VALIDATOR)
                cache_path.mkdir(parents=True, exist_ok=True)
                args.append(
                    f"--validator_cache={CACHE_PATH_VALIDATOR}{data.validator_cache_file}"
                )

        # Run task asynchroniously
        self._running_task_checker = await asyncio.create_subprocess_exec(
            os.path.abspath(self.__csaf_checker_path()),
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=CSAF_BINARY_PATH,
            env=None,
        )

    async def __terminate_asyncio_task(self):
        if self._running_task_checker is None:
            return

        logger.info("Terminating running csaf checker task")
        try:
            self._running_task_checker.terminate()
            return
        except Exception:
            logger.exception("Failed to terminate subprocess on stop request")
        try:
            await self._running_task_checker.wait()
            await self._running_task_checker.terminate()
        except Exception:
            pass

    async def run(self, data: Domain_Task_Data) -> (int, str):
        """
        Starts asynchronous task in which csaf checker be called.
        Reacts to outside signals.

        Returns a tuple. The integer represents the exit status. The string
        represents an error message.

        The exit status codes represent the following states:
            0 = Success
            1 = Failure
            2 = Controlled Termination (iE. User aborts the running task)
        """
        try:
            # create subprocess, merge stderr into stdout for unified streaming
            await self.__start_asyncio_task(data)
            logger.info(f"Async CSAF checker task for domain {data.domain}")

            # Stream output lines as they come
            exitCode = 0
            errorMsg = ""
            inJSONStructure = False
            while True:
                # Check signals
                # - Termination Signal
                if self._signal_stop:
                    logger.info(f"Stop csaf checker task for domain {data.domain}")
                    await self.__terminate_asyncio_task()

                    self._signal_stop = False
                    exitCode = 2
                    break

                # - Restart Signal
                if self._signal_restart:
                    logger.info(f"Restart csaf checker task for domain {data.domain}")

                    await self.__start_asyncio_task(data)

                    self._signal_restart = False
                    continue

                # - Pause Signal
                if self._signal_paused:
                    pause_timer = self._max_wait_time
                    logger.info(f"Pause csaf checker task for domain {data.domain}")
                    if self._running_task_checker.pid is not None:
                        try:
                            os.kill(self._running_task_checker.pid, signal.SIGSTOP)
                        except Exception as e:
                            logger.info(f"SIGSTOP failed: {e}")
                            return (1, f"Error: Couldn't pause domain task: {e}")

                    while self._signal_paused is True:
                        await asyncio.sleep(self._wait_time_interval)
                        pause_timer -= self._wait_time_interval

                        if pause_timer <= 0:
                            await self.__terminate_asyncio_task()
                            exitCode = 1
                            errorMsg = "Error: Time Out: Domain task was paused for too long"
                            break

                    if exitCode != 0:
                        break

                    # reiterate early in case restart or stop has been signaled while task was paused
                    if self._signal_restart or self._signal_stop:
                        continue

                    logger.info(f"Continue csaf checker task for domain {data.domain}")
                    if self._running_task_checker.pid is not None:
                        try:
                            os.kill(self._running_task_checker.pid, signal.SIGCONT)
                        except Exception as e:
                            logger.info(f"SIGCONT failed: {e}")
                            exitCode = 1
                            errorMsg = f"Error: Couldn't unpause domain task: {e}"
                            break

                    self._signal_paused = False

                # Interprete output
                line = await self._running_task_checker.stdout.readline()

                self._loop_step = self._loop_step + 1

                if not line:
                    break
                decoded_line = line.decode(errors="replace").rstrip("\n")

                # Once a single '{' is read, it is assumed that the csaf results are printed out
                inJSONStructure = inJSONStructure or (decoded_line == "{")
                if inJSONStructure:
                    # Result Line
                    data.csaf_checker_output_result += decoded_line + "\n"
                else:
                    # Runtime Line
                    data.csaf_checker_output_runtime_log.append(decoded_line)

            if exitCode != 0:
                logger.info(f"Task exited with code {exitCode} and error message: {errorMsg}")
                return (exitCode, errorMsg)

            # Get exit codes
            exitCode = await self._running_task_checker.wait()
            logger.info(f"Task done with exit code {exitCode}")

            if exitCode == 0:
                # Success
                return (0, "")
            else:
                return (1, f"CSAF Process ended with status code: {exitCode}")

        except asyncio.CancelledError as e:
            # If the coroutine is cancelled, try to terminate the process
            await self.__terminate_asyncio_task()
            return (1, f"CSAF Process cancelled with error: {e}")

        except FileNotFoundError as e:
            # Binary not found
            return (
                1,
                f"CSAF Checker Binary not found: {self.__csaf_checker_path()}, error: {e}",
            )

        except Exception as e:
            # Unexpected error running the process
            # Try to terminate the process
            await self.__terminate_asyncio_task()
            return (1, f"CSAF Checker error: {e}")
