# Manages slots and thereby threading.
# May start and stop running threads/slots.
# Checks if all slots are already in use, if a requested
# domain has already been requested by another user at the same time,
# or if there are orphaned slots that may be ended early

# Involved in: 5, 9, 14, 16, 22

from __future__ import annotations

from typing import Annotated, Optional

from pydantic import Field

from ..router.scan_request import ScanRequest
from .slot import Slot


class Slot_Manager:
    _instance: Annotated[
        Optional[Slot_Manager], Field(description="Singleton instance")
    ] = None

    slot_amount: Annotated[
        int, Field(description="Amount of slots that should be available at runtime")
    ] = 10
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
        for _ in range(self.slot_amount):
            self.slots.append(Slot())

    async def start_domain_task(self, request: ScanRequest) -> Slot:
        # Find available slot
        available_slot = self.find_first_available_slot()
        if available_slot is None:
            # Throw some kind of error
            return None

        # Start Checker
        await available_slot.start_domain_task(request)

        return available_slot

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
