# Manages slots and thereby threading.
# May start and stop running threads/slots.
# Checks if all slots are already in use, if a requested
# domain has already been requested by another user at the same time,
# or if there are orphaned slots that may be ended early

# Involved in: 5, 9, 14, 16, 22

from __future__ import annotations

import logging
import os
from typing import Annotated, Optional

from pydantic import Field

from ..database.database import Database_Manager
from ..router.scan_request import ScanRequest
from .slot import Slot

logger = logging.getLogger(__name__)


class Slot_Manager:
    _instance: Annotated[
        Optional[Slot_Manager], Field(description="Singleton instance")
    ] = None

    slot_amount: Annotated[
        int, Field(description="Amount of slots that should be available at runtime")
    ] = int(os.environ.get("SCAN_SLOTS", "10"))
    slots: list[
        Annotated[Slot, Field(description="List of slots for domain task execution")]
    ] = []

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # Avoid reinitialization
        if getattr(self, "_initialized", False):
            return
        self._initialized = True

        # Setup slot manager
        self.slots = []
        for i in range(self.slot_amount):
            self.slots.append(Slot.create(i))

    def start_domain_task(self, request: ScanRequest) -> str:
        """
        Starts a domain task for the requested domain.
        If a domain task for the requested domain has already been started or recently cached, no new domain task will be started

        Started domain tasks are associated with a slot. The associated slot is blocked until the domain task is done or has been orphaned
        Only a fixed amount of slots are available for processing at once

        Returns uuid of relevant domain task.
        """
        # Check database cache first
        if not request.skip_cache:
            cached_task_data = Database_Manager().load_task_by_domain(request.domain)
            if cached_task_data is not None:
                if cached_task_data.cache_is_outdated():
                    logger.info(
                        f"Found {request.domain} in cache but cache is outdated. UUID : {cached_task_data.uuid}"
                    )
                else:
                    logger.info(
                        f"Found {request.domain} in cache. UUID : {cached_task_data.uuid}"
                    )
                    return cached_task_data.uuid

        # Find available slot
        available_slot = self.find_first_available_slot()
        if available_slot is None:
            # FIXME: Throw some kind of error
            logger.info("No available slot found")
            return ""

        logger.info(
            f"For scan request of domain {request.domain}, slot {available_slot.id} is available"
        )

        # Start Checker
        domain_task_uuid = available_slot.start_domain_task(request)

        return domain_task_uuid

    def get_slot_by_task_id(self, task_id: str) -> Slot:
        for slot in self.slots:
            if slot.running_task is not None:
                if str(slot.running_task.get_data(False).uuid) == task_id:
                    return slot
        return None

    def find_first_available_slot(self) -> Slot:
        # First check if any slot is available outright
        for slot in self.slots:
            if slot.is_available():
                return slot

        # Next check if any slot has a running task that is orphaned
        for slot in self.slots:
            if slot.is_task_orphaned():
                return slot

        return None
