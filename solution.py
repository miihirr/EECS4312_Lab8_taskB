## Student Name: Mihir Patel
## Student ID: 219695808

"""
Task B: Event Registration with Waitlist (Stub)
In this lab, you will design and implement an Event Registration with Waitlist system using an LLM assistant as your primary programming collaborator. 
You are asked to implement a Python module that manages registration for a single event with a fixed capacity. 
The system must:
•	Accept a fixed capacity.
•	Register users until capacity is reached.
•	Place additional users into a FIFO waitlist.
•	Automatically promote the earliest waitlisted user when a registered user cancels.
•	Prevent duplicate registrations.
•	Allow users to query their current status.

The system must ensure that:
•	The number of registered users never exceeds capacity.
•	Waitlist ordering preserves FIFO behavior.
•	Promotions occur deterministically under identical operation sequences.

The module must preserve the following invariants:
•	A user may not appear more than once in the system.
•	A user may not simultaneously exist in multiple states.
•	The system state must remain consistent after every operation.

The system must correctly handle non-trivial scenarios such as:
•	Multiple cancellations in sequence.
•	Users attempting to re-register after canceling.
•	Waitlisted users canceling before promotion.
•	Capacity equal to zero.
•	Simultaneous or rapid consecutive operations.
•	Queries during state transitions.

The output consists of the updated registration state and ordered lists of registered and waitlisted users after each operation.
"""

from dataclasses import dataclass
from typing import List, Optional


class DuplicateRequest(Exception):
    """Raised if a user tries to register but is already registered or waitlisted."""
    pass


class NotFound(Exception):
    """Raised if a user cannot be found for cancellation (if required by handout)."""
    pass


@dataclass(frozen=True)
class UserStatus:
    """
    state:
      - "registered"
      - "waitlisted"
      - "none"
    position: 1-based waitlist position if waitlisted; otherwise None
    """
    state: str
    position: Optional[int] = None


class EventRegistration:
    """
    Manages event registration with a fixed capacity and FIFO waitlist.
    Ensures users are not duplicated and capacity is never exceeded.
    """

    def __init__(self, capacity: int) -> None:
        """
        Args:
            capacity: maximum number of registered users (>= 0)
        """
        self.capacity = capacity
        self.registered = []  # List of registered user_ids in order
        self.waitlist = []    # List of waitlisted user_ids in FIFO order
        self.user_locations = {}  # Track if user is "registered", "waitlisted", or doesn't exist

    def register(self, user_id: str) -> UserStatus:
        """
        Register a user:
          - if capacity available -> registered
          - else -> waitlisted (FIFO)

        Raises:
            DuplicateRequest if user already exists (registered or waitlisted)
        """
        # Check if user already exists
        if user_id in self.user_locations:
            raise DuplicateRequest(f"User {user_id} already exists in system")

        # If we have space, register directly
        if len(self.registered) < self.capacity:
            self.registered.append(user_id)
            self.user_locations[user_id] = "registered"
            return UserStatus("registered")
        else:
            # Otherwise add to waitlist
            self.waitlist.append(user_id)
            position = len(self.waitlist)  # 1-based position
            self.user_locations[user_id] = "waitlisted"
            return UserStatus("waitlisted", position)

    def cancel(self, user_id: str) -> None:
        """
        Cancel a user:
          - if registered -> remove and promote earliest waitlisted user (if any)
          - if waitlisted -> remove from waitlist
          
        Raises:
            NotFound if user is not in the system
        """
        if user_id not in self.user_locations:
            raise NotFound(f"User {user_id} not found")

        location = self.user_locations[user_id]

        if location == "registered":
            # Remove from registered
            self.registered.remove(user_id)
            del self.user_locations[user_id]

            # Promote first waitlisted user if any
            if self.waitlist:
                promoted_user = self.waitlist.pop(0)
                self.registered.append(promoted_user)
                self.user_locations[promoted_user] = "registered"

        elif location == "waitlisted":
            # Remove from waitlist
            self.waitlist.remove(user_id)
            del self.user_locations[user_id]
            # Update positions for remaining waitlisted users
            # (positions are calculated dynamically in status())

    def status(self, user_id: str) -> UserStatus:
        """
        Return status of a user:
          - registered
          - waitlisted with position (1-based)
          - none
        """
        if user_id not in self.user_locations:
            return UserStatus("none")

        location = self.user_locations[user_id]

        if location == "registered":
            return UserStatus("registered")
        else:  # waitlisted
            # Calculate position (1-based)
            position = self.waitlist.index(user_id) + 1
            return UserStatus("waitlisted", position)

    def snapshot(self) -> dict:
        """
        Return a deterministic snapshot of internal state.
        """
        return {
            "registered": self.registered.copy(),
            "waitlist": self.waitlist.copy()
        }