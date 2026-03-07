import pytest

from solution import EventRegistration, UserStatus, DuplicateRequest, NotFound


def test_register_until_capacity_then_waitlist_fifo_positions():
    er = EventRegistration(capacity=2)

    s1 = er.register("u1")
    s2 = er.register("u2")
    s3 = er.register("u3")
    s4 = er.register("u4")

    assert s1 == UserStatus("registered")
    assert s2 == UserStatus("registered")
    assert s3 == UserStatus("waitlisted", 1)
    assert s4 == UserStatus("waitlisted", 2)

    snap = er.snapshot()
    assert snap["registered"] == ["u1", "u2"]
    assert snap["waitlist"] == ["u3", "u4"]


def test_cancel_registered_promotes_earliest_waitlisted_fifo():
    er = EventRegistration(capacity=1)
    er.register("u1")
    er.register("u2")  # waitlist
    er.register("u3")  # waitlist

    er.cancel("u1")  # should promote u2

    assert er.status("u1") == UserStatus("none")
    assert er.status("u2") == UserStatus("registered")
    assert er.status("u3") == UserStatus("waitlisted", 1)

    snap = er.snapshot()
    assert snap["registered"] == ["u2"]
    assert snap["waitlist"] == ["u3"]


def test_duplicate_register_raises_for_registered_and_waitlisted():
    er = EventRegistration(capacity=1)
    er.register("u1")
    with pytest.raises(DuplicateRequest):
        er.register("u1")

    er.register("u2")  # waitlisted
    with pytest.raises(DuplicateRequest):
        er.register("u2")


def test_waitlisted_cancel_removes_and_updates_positions():
    er = EventRegistration(capacity=1)
    er.register("u1")
    er.register("u2")  # waitlist pos1
    er.register("u3")  # waitlist pos2

    er.cancel("u2")    # remove from waitlist

    assert er.status("u2") == UserStatus("none")
    assert er.status("u3") == UserStatus("waitlisted", 1)

    snap = er.snapshot()
    assert snap["registered"] == ["u1"]
    assert snap["waitlist"] == ["u3"]


def test_capacity_zero_all_waitlisted_and_promotion_never_happens():
    er = EventRegistration(capacity=0)
    assert er.register("u1") == UserStatus("waitlisted", 1)
    assert er.register("u2") == UserStatus("waitlisted", 2)

    # No one can ever be registered when capacity=0
    assert er.status("u1") == UserStatus("waitlisted", 1)
    assert er.status("u2") == UserStatus("waitlisted", 2)
    assert er.snapshot()["registered"] == []

    # Cancel unknown should raise NotFound
    with pytest.raises(NotFound):
        er.cancel("missing")



#################################################################################
# Additional Edge Case Tests
#################################################################################

def test_multiple_sequential_cancellations():
    """Test cascading promotions from multiple cancellations"""
    er = EventRegistration(capacity=2)
    er.register("alice")
    er.register("bob")
    er.register("charlie")  # waitlist pos 1
    er.register("dave")     # waitlist pos 2

    # Cancel registered user -> promote charlie
    er.cancel("alice")
    assert er.status("charlie") == UserStatus("registered")
    assert er.status("dave") == UserStatus("waitlisted", 1)

    # Cancel another registered user -> promote dave
    er.cancel("bob")
    assert er.status("dave") == UserStatus("registered")
    assert er.snapshot()["waitlist"] == []


def test_user_cancel_then_reregister():
    """Test user canceling and then registering again"""
    er = EventRegistration(capacity=1)
    er.register("alice")
    er.register("bob")  # waitlist

    er.cancel("alice")
    
    # Alice status should be none
    assert er.status("alice") == UserStatus("none")
    assert er.status("bob") == UserStatus("registered")

    # Alice should be able to register again
    result = er.register("alice")
    assert result == UserStatus("waitlisted", 1)
    assert er.status("alice") == UserStatus("waitlisted", 1)


def test_status_query_nonexistent_user():
    """Test status query for user never registered"""
    er = EventRegistration(capacity=2)
    er.register("alice")
    
    assert er.status("unknown") == UserStatus("none")
    assert er.status("unknown").position is None


def test_cancel_nonexistent_user_raises_notfound():
    """Test canceling a user that doesn't exist"""
    er = EventRegistration(capacity=1)
    er.register("alice")
    
    with pytest.raises(NotFound):
        er.cancel("nonexistent")


def test_waitlist_user_cancel_then_promotion_still_works():
    """Test that canceling a waitlist user doesn't break promotion chain"""
    er = EventRegistration(capacity=1)
    er.register("alice")    # registered
    er.register("bob")      # waitlist pos 1
    er.register("charlie")  # waitlist pos 2
    er.register("dave")     # waitlist pos 3

    # Bob cancels before being promoted
    er.cancel("bob")
    assert er.status("bob") == UserStatus("none")
    assert er.status("charlie") == UserStatus("waitlisted", 1)
    assert er.status("dave") == UserStatus("waitlisted", 2)

    # Alice cancels, should promote charlie (not bob who's gone)
    er.cancel("alice")
    assert er.status("charlie") == UserStatus("registered")
    assert er.status("dave") == UserStatus("waitlisted", 1)


def test_large_capacity_no_waitlist():
    """Test system with large capacity where no one goes to waitlist"""
    er = EventRegistration(capacity=10)
    
    for i in range(10):
        result = er.register(f"user{i}")
        assert result.state == "registered"
    
    # 11th user should go to waitlist
    result = er.register("user10")
    assert result == UserStatus("waitlisted", 1)


def test_snapshot_reflects_current_state():
    """Test that snapshot always shows current accurate state"""
    er = EventRegistration(capacity=2)
    er.register("a")
    er.register("b")
    er.register("c")
    er.register("d")

    snap1 = er.snapshot()
    assert len(snap1["registered"]) == 2
    assert len(snap1["waitlist"]) == 2

    er.cancel("a")
    snap2 = er.snapshot()
    assert snap2["registered"] == ["b", "c"]
    assert snap2["waitlist"] == ["d"]


def test_capacity_one_single_registered_continuous_promotion():
    """Test capacity=1 with continuous promotion chain"""
    er = EventRegistration(capacity=1)
    users = ["u1", "u2", "u3", "u4", "u5"]
    
    for user in users:
        er.register(user)
    
    # Register all 5, only u1 registered, rest waitlisted
    assert er.status("u1") == UserStatus("registered")
    for i, user in enumerate(users[1:], 1):
        assert er.status(user) == UserStatus("waitlisted", i)
    
    # Cancel u1, u2 gets promoted
    er.cancel("u1")
    assert er.status("u2") == UserStatus("registered")
    assert er.status("u3") == UserStatus("waitlisted", 1)