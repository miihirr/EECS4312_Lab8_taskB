## Student Name: Mihir Patel
## Student ID: 219695808

"""
Task B: Event Registration with Waitlist
Lab 9 – Persona-Constrained Implementation

This module manages registration for a single event with a fixed capacity.
It supports two user personas:
  - Jane Adams (Primary User): Expects reliable, predictable behavior with
    minimal interaction and concise outputs.
  - Mo Rodriguez (Edge User): Requires explicit explanations for every system
    decision and deterministic handling of edge cases.

The system must:
  - Accept a fixed capacity.
  - Register users until capacity is reached.
  - Place additional users into a FIFO waitlist.
  - Automatically promote the earliest waitlisted user when a registered user cancels.
  - Prevent duplicate registrations.
  - Allow users to query their current status.
  - Return clear explanation messages for every operation (persona constraint C5).
  - Handle all edge cases explicitly without silent failure (persona constraint C6).
"""

from dataclasses import dataclass
from typing import List, Optional


class DuplicateRequest(Exception):
    """Raised if a user tries to register but is already registered or waitlisted."""
    pass


class NotFound(Exception):
    """Raised if a user cannot be found for cancellation."""
    pass


@dataclass(frozen=True)
class UserStatus:
    """
    Represents the status of a user in the system.

    state:
      - "registered"  : user is registered for the event
      - "waitlisted"  : user is on the waitlist
      - "none"        : user is not in the system
    position: 1-based waitlist position if waitlisted; otherwise None
    explanation: human-readable message describing the result (supports Mo's accessibility needs)
    """
    state: str
    position: Optional[int] = None
    explanation: Optional[str] = None


class EventRegistration:
    """
    Manages event registration with a fixed capacity and FIFO waitlist.

    Persona constraints enforced:
      C1: Registered count never exceeds capacity.
      C2: Waitlist preserves FIFO order.
      C3: Promotions are deterministic and immediate.
      C4: No duplicate users in the system.
      C5: Every operation returns a concise explanation message.
      C6: Edge cases handled explicitly with clear feedback.
      C7: No duplicate or redundant messages per operation.
      C8: Identical operation sequences produce identical results.
    """

    def __init__(self, capacity: int) -> None:
        """
        Args:
            capacity: maximum number of registered users (>= 0)
        """
        self.capacity = capacity
        self.registered: List[str] = []     # Registered user_ids in order
        self.waitlist: List[str] = []       # Waitlisted user_ids in FIFO order
        self.user_locations: dict = {}      # Maps user_id -> "registered" | "waitlisted"

    def register(self, user_id: str) -> UserStatus:
        """
        Register a user for the event.

        - If capacity is available, the user is registered.
        - If capacity is full, the user is added to the FIFO waitlist.
        - If the user already exists, raises DuplicateRequest.

        Returns:
            UserStatus with state, position (if waitlisted), and explanation message.
        """
        # C4: Prevent duplicate registration
        if user_id in self.user_locations:
            current = self.user_locations[user_id]
            raise DuplicateRequest(
                f"User '{user_id}' is already {current}. Duplicate registration is not allowed."
            )

        # C1: Never exceed capacity
        if len(self.registered) < self.capacity:
            self.registered.append(user_id)
            self.user_locations[user_id] = "registered"
            return UserStatus(
                state="registered",
                explanation=f"User '{user_id}' has been successfully registered for the event."
            )
        else:
            # C2: Maintain FIFO waitlist order
            self.waitlist.append(user_id)
            position = len(self.waitlist)
            self.user_locations[user_id] = "waitlisted"
            return UserStatus(
                state="waitlisted",
                position=position,
                explanation=f"Event is full. User '{user_id}' has been added to the waitlist at position {position}."
            )

    def cancel(self, user_id: str) -> str:
        """
        Cancel a user's registration or waitlist entry.

        - If the user is registered, they are removed and the earliest
          waitlisted user is promoted (C3: immediate, deterministic promotion).
        - If the user is waitlisted, they are removed from the waitlist.
        - If the user is not found, raises NotFound.

        Returns:
            A human-readable explanation string describing what happened (C5, C6).
        """
        # C6: Explicit handling of non-existent user
        if user_id not in self.user_locations:
            raise NotFound(
                f"User '{user_id}' was not found in the system. No action was taken."
            )

        location = self.user_locations[user_id]

        if location == "registered":
            self.registered.remove(user_id)
            del self.user_locations[user_id]

            # C3: Promote first waitlisted user immediately
            if self.waitlist:
                promoted_user = self.waitlist.pop(0)
                self.registered.append(promoted_user)
                self.user_locations[promoted_user] = "registered"
                return (
                    f"User '{user_id}' has been removed from registered. "
                    f"User '{promoted_user}' has been promoted from the waitlist to registered."
                )
            else:
                return (
                    f"User '{user_id}' has been removed from registered. "
                    f"No users on the waitlist to promote."
                )

        elif location == "waitlisted":
            self.waitlist.remove(user_id)
            del self.user_locations[user_id]
            return (
                f"User '{user_id}' has been removed from the waitlist. "
                f"Remaining waitlisted users have shifted up in position."
            )

    def status(self, user_id: str) -> UserStatus:
        """
        Query the current status of a user.

        Returns:
            UserStatus with state, position (if waitlisted), and explanation.
        """
        if user_id not in self.user_locations:
            return UserStatus(
                state="none",
                explanation=f"User '{user_id}' is not found in the system."
            )

        location = self.user_locations[user_id]

        if location == "registered":
            return UserStatus(
                state="registered",
                explanation=f"User '{user_id}' is currently registered for the event."
            )
        else:
            position = self.waitlist.index(user_id) + 1
            return UserStatus(
                state="waitlisted",
                position=position,
                explanation=f"User '{user_id}' is on the waitlist at position {position}."
            )

    def snapshot(self) -> dict:
        """
        Return a deterministic snapshot of the current system state.
        Useful for debugging and verifying system consistency (C8).
        """
        return {
            "registered": self.registered.copy(),
            "waitlist": self.waitlist.copy()
        }