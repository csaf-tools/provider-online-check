# Interface to call, communicate with and save results of csaf checker

# Involved in: 7, 8, 9
from ..database.domain_task_data import Domain_Task_Data

import asyncio
import os
import logging

logger = logging.getLogger(__name__)

CSAF_BINARY_PATH = "./bin/csaf-binary/bin-linux-amd64/"
CSAF_CHECKER_BINARY = "csaf_checker"
CSAF_VALIDATOR_BINARY = "csaf_validator"


class CSAF_Checker():

    @classmethod
    async def run(cls, data: Domain_Task_Data):
        csaf_checker_path = CSAF_BINARY_PATH + CSAF_CHECKER_BINARY

        try:
            # create subprocess, merge stderr into stdout for unified streaming
            args = ["--verbose", data.domain]
            task_checker = await asyncio.create_subprocess_exec(
                os.path.abspath(csaf_checker_path),
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=CSAF_BINARY_PATH,
                env=None,
            )
            logger.info(f"Async Domain Task for domain {data.domain}")

            # Stream output lines as they come
            assert task_checker.stdout is not None
            while True:
                line = await task_checker.stdout.readline()
                if not line:
                    break
                decoded = line.decode(errors="replace").rstrip("\n")
                # append to logs
                data.csaf_checker_output.append(decoded)
                # logger.info(decoded)

                # FIXME
                # Notify client socket

            returncode = await task_checker.wait()
            logger.info(f"Task done with returncode {returncode}")

            if returncode == 0:
                return True
            else:
                return False

        except asyncio.CancelledError:
            # If the coroutine is cancelled, try to terminate the process
            try:
                task_checker.terminate()
            except Exception:
                pass

            # FIXME
            # Throw Interrupt

            raise  # re-raise so callers know cancellation happened

        except FileNotFoundError:
            # binary not found
            raise (f"CSAF Checker Binary not found: {csaf_checker_path}")

        except Exception as e:
            # Unexpected error running the process
            raise (f"CSAF Checker error: {e}")
