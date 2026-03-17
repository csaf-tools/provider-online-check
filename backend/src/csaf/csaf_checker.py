# Interface to call, communicate with and save results of csaf checker

# Involved in: 7, 8, 9
from ..database.domain_task_data import Domain_Task_Data

from typing import Optional

import asyncio
import os
import logging
import signal
import hashlib

logger = logging.getLogger(__name__)

CSAF_BINARY_PATH = "/app/bin/csaf-binary/bin-linux-amd64/"
CSAF_CHECKER_BINARY = "csaf_checker"
CACHE_PATH_VALIDATOR = "/app/store/validator/cache/"

PAUSE_TIME_MAX_BEFORE_RESET=100
PAUSE_TIME_INTERVAL=0.2

class CSAF_Checker():

    _signal_paused: bool = False
    _signal_stop: bool = False
    _signal_restart: bool = False

    _running_task_checker: Optional[asyncio.subprocess.Process] = None

    def pause(self):
        self._signal_paused = True

    def unpause(self):
        self._signal_paused = False

    def stop(self):
        self._signal_stop = True

    def restart(self):
        self._signal_restart = True

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
            args.append(f"--validator_cache={CACHE_PATH_VALIDATOR}{data.validator_cache_file}")

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
        except Exception:
            logger.exception("Failed to terminate subprocess on stop request")
        try:
            await self._running_task_checker.wait()
        except Exception:
            pass

    async def run(self, data: Domain_Task_Data, task: Domain_Task):

        try:
            # create subprocess, merge stderr into stdout for unified streaming
            self.__start_asyncio_task(data)
            logger.info(f"Async CSAF checker task for domain {data.domain}")

            # Stream output lines as they come

            inJSONStructure = False
            while True:
                # Check signals

                # - Termination Signal
                if self._signal_stop:
                    logger.info(f"Stop csaf checker task for domain {data.domain}")
                    self.__terminate_asyncio_task()
                    # FIXME
                    # Add termination error

                    self._signal_stop = False
                    return False

                # - Restart Signal
                if self._signal_restart:
                    logger.info(f"Restart csaf checker task for domain {data.domain}")

                    self.__start_asyncio_task(data)

                    self._signal_restart = False
                    continue

                # - Pause Signal
                if self._signal_paused:
                    max_wait_time = PAUSE_TIME_MAX_BEFORE_RESET
                    wait_time_interval = PAUSE_TIME_INTERVAL

                    logger.info(f"Pause csaf checker task for domain {data.domain}")
                    if self._running_task_checker.pid is not None:
                        try:
                            os.kill(self._running_task_checker.pid, signal.SIGSTOP)
                        except Exception as e:
                            logger.debug(f"SIGSTOP failed: {e}")

                    while self._pause_event.is_set():
                        await asyncio.sleep(wait_time_interval)
                        max_wait_time -= wait_time_interval

                        if max_wait_time < 0:
                            self.__terminate_asyncio_task()
                            # FIXME
                            # Add timeout error
                            return False

                    # stop early in case restart or stop has been signaled while task was paused
                    if self._signal_restart or self._signal_stop:
                        continue

                    logger.info(f"Continue csaf checker task for domain {data.domain}")
                    if self._running_task_checker.pid is not None:
                        try:
                            os.kill(self._running_task_checker.pid, signal.SIGCONT)
                        except Exception as e:
                            logger.debug(f"SIGCONT failed: {e}")

                    self._signal_paused = False

                # Interprete output
                line = await self._running_task_checker.stdout.readline()
                if not line:
                    break
                decoded_line = line.decode(errors="replace").rstrip("\n")

                # Once a single '{' is read, it is assumed that the csaf results are printed out
                inJSONStructure = (inJSONStructure or (decoded_line == "{"))
                if inJSONStructure:
                    # Result Line
                    data.csaf_checker_output_result += (decoded_line + "\n")
                else:
                    # Runtime Line
                    data.csaf_checker_output_runtime_log.append(decoded_line)

            # Done
            returncode = await self._running_task_checker.wait()
            logger.info(f"Task done with returncode {returncode}")

            if returncode == 0:
                # Write Task
                task.on_checker_done()
            else:
                task.on_error(f"CSAF Process ended with status code: {returncode}")

        except asyncio.CancelledError as e:

            task.on_error(f"CSAF Process cancelled with error: {e}")

            # If the coroutine is cancelled, try to terminate the process
            try:
                self.__terminate_asyncio_task()
            except Exception:
                pass
            pass

        except FileNotFoundError as e:
            # Binary not found
            task.on_error(f"CSAF Checker Binary not found: {self.__csaf_checker_path()}, error: {e}")

            pass

        except Exception as e:
            # Unexpected error running the process
            task.on_error(f"CSAF Checker errror: {e}")

            # Try to terminate the process
            try:
                self.__terminate_asyncio_task()
            except Exception:
                pass
            pass
