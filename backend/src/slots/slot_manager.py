# Manages slots and thereby threading.
# May start and stop running threads/slots.
# Checks if all slots are already in use, if a requested
# domain has already been requested by another user at the same time,
# or if there are orphaned slots that may be ended early

# Involved in: 5, 9, 14, 16, 22

from fastapi import FastAPI
from typing import Annotated
from pydantic import BaseModel, Field, WithJsonSchema

from .slot import Slot
from ..router.router import ScanRequest

class Slot_Manager:
    _instance:      Annotated[Slot_Manager, Field(description="Singleton instance"), Field(default=None)]

    slot_amount:    Annotated[int, Field(description="Amount of slots that should be available at runtime"), Field(default=10)]
    slots:          list[Annotated[Slot,  Field(description="List of slots for domain task execution")]]

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, value):
        # Setup slot manager
        for i in enumerate(slot_amount):
            slots[i] = Slot()

    async def start_domain_task(self, request: ScanRequest):
        # Find available slot
        available_slot = this.find_first_available_slot()
        if available_slot == None:
            # Throw some kind of error
            return

        # Start Checker
        available_slot.start_domain_task(request)

    async def find_first_available_slot(self) -> Slot:
        return None

