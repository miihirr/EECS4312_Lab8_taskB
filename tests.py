## Student Name: Mihir Patel
## Student ID: 219695808

import pytest
from solution import EventRegistration, UserStatus, DuplicateRequest, NotFound


# Covers C1, C2, AC1, AC2
# Verifies that users register up to capacity, then go to FIFO waitlist with correct positions.
def test_register_until_capacity_then_waitlist():
    er = EventRegistration(capacity=2)

    s1 = er.register("u1")
    s2 = er.register("u2")
    s3 = er.register("u3")
    s4 = er.register("u4")

    # Registered users should not exceed capacity (C1)
    assert s1.state == "registered"
    assert s2.state == "registered"
    assert s3.state == "waitlisted"
    assert s3.position == 1
    assert s4.state == "waitlisted"
    assert s4.position == 2

    # Waitlist order must be FIFO (C2)
    snap = er.snapshot()
    assert snap["registered"] == ["u1", "u2"]
    assert snap["waitlist"] == ["u3", "u4"]
    assert len(snap["registered"]) <= 2  # AC1


# Covers C3, AC3
# Verifies that cancelling a registered user immediately promotes the earliest waitlisted user.
def test_cancel_promotes_earliest_waitlisted_user():
    er = EventRegistration(capacity=1)
    er.register("u1")
    er.register("u2")  # waitlist pos 1
    er.register("u3")  # waitlist pos 2

    explanation = er.cancel("u1")

    # u2 should be promoted (C3: deterministic, immediate promotion)
    assert er.status("u1").state == "none"
    assert er.status("u2").state == "registered"
    assert er.status("u3").state == "waitlisted"
    assert er.status("u3").position == 1

    # Explanation should mention the promotion (C5)
    assert "u2" in explanation
    assert "promoted" in explanation.lower()


# Covers C4, AC4
# Verifies that duplicate registration raises DuplicateRequest for both registered and waitlisted users.
def test_duplicate_registration_raises_error():
    er = EventRegistration(capacity=1)
    er.register("u1")

    # Duplicate registered user
    with pytest.raises(DuplicateRequest):
        er.register("u1")

    # Duplicate waitlisted user
    er.register("u2")  # goes to waitlist
    with pytest.raises(DuplicateRequest):
        er.register("u2")


# Covers C5, AC5, AC6
# Verifies that register and cancel return human-readable explanation messages (Mo's accessibility need).
def test_explanation_messages_are_returned():
    er = EventRegistration(capacity=1)

    # Register should return explanation (AC5)
    result = er.register("alice")
    assert result.explanation is not None
    assert "alice" in result.explanation
    assert len(result.explanation) > 0

    # Waitlisted registration should explain position
    result2 = er.register("bob")
    assert result2.explanation is not None
    assert "waitlist" in result2.explanation.lower()

    # Cancel should return explanation (AC6)
    explanation = er.cancel("alice")
    assert explanation is not None
    assert "alice" in explanation
    assert "bob" in explanation  # Should mention promotion


# Covers C5, C7, AC6
# Verifies cancelling a waitlisted user returns an explanation and does not produce extra messages.
def test_cancel_waitlisted_user_returns_explanation():
    er = EventRegistration(capacity=1)
    er.register("u1")
    er.register("u2")  # waitlist pos 1
    er.register("u3")  # waitlist pos 2

    explanation = er.cancel("u2")

    # Should explain removal (C5)
    assert "u2" in explanation
    assert "removed" in explanation.lower()

    # Remaining waitlisted user shifts up (C2)
    assert er.status("u3").state == "waitlisted"
    assert er.status("u3").position == 1
    assert er.status("u2").state == "none"


# ---- EDGE CASE TESTS ----

# Covers C6, AC7 — Edge Case EC1
# Verifies that when capacity is zero, all users go to waitlist and no one is ever registered.
def test_edge_case_zero_capacity():
    er = EventRegistration(capacity=0)

    s1 = er.register("u1")
    s2 = er.register("u2")

    assert s1.state == "waitlisted"
    assert s1.position == 1
    assert s2.state == "waitlisted"
    assert s2.position == 2

    # No one should be registered (AC7)
    snap = er.snapshot()
    assert snap["registered"] == []
    assert len(snap["waitlist"]) == 2

    # Cancelling from waitlist should work cleanly
    explanation = er.cancel("u1")
    assert er.status("u1").state == "none"
    assert er.status("u2").position == 1
    # No promotion should happen since capacity is 0
    assert snap["registered"] == []


# Covers C6, AC8 — Edge Case EC4
# Verifies that a user who cancels can re-register without error.
def test_edge_case_reregister_after_cancel():
    er = EventRegistration(capacity=1)
    er.register("alice")
    er.register("bob")  # waitlist

    er.cancel("alice")

    # alice should be gone
    assert er.status("alice").state == "none"
    # bob should be promoted
    assert er.status("bob").state == "registered"

    # alice re-registers — should be allowed (EC4, AC8)
    result = er.register("alice")
    assert result.state == "waitlisted"
    assert result.position == 1
    assert er.status("alice").state == "waitlisted"


# Covers C6, C8 — Edge Case EC2
# Verifies multiple sequential cancellations with correct FIFO promotions.
def test_edge_case_multiple_cancellations():
    er = EventRegistration(capacity=2)
    er.register("a")
    er.register("b")
    er.register("c")  # waitlist pos 1
    er.register("d")  # waitlist pos 2

    # Cancel a -> promote c
    explanation1 = er.cancel("a")
    assert er.status("c").state == "registered"
    assert er.status("d").state == "waitlisted"
    assert er.status("d").position == 1
    assert "c" in explanation1  # promotion explained

    # Cancel b -> promote d
    explanation2 = er.cancel("b")
    assert er.status("d").state == "registered"
    assert er.snapshot()["waitlist"] == []
    assert "d" in explanation2  # promotion explained

    # C8: System is consistent after all operations
    snap = er.snapshot()
    assert snap["registered"] == ["c", "d"]
    assert snap["waitlist"] == []


# Covers C6 — Edge Case EC5
# Verifies that cancelling a user not in the system raises NotFound with an explanation.
def test_edge_case_cancel_nonexistent_user():
    er = EventRegistration(capacity=1)
    er.register("alice")

    with pytest.raises(NotFound) as exc_info:
        er.cancel("ghost")

    # C6: Explicit error with explanation
    assert "ghost" in str(exc_info.value)
