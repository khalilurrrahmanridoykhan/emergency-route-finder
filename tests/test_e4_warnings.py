"""Warning logic for the emergency route record."""
from e4_warnings import build_warnings


def test_no_warnings_for_an_easy_unaffected_point():
    w = build_warnings(20, 21, 5, 5, 25, 120, False)
    assert w == []


def test_no_route_in_either_season():
    w = build_warnings(None, None, None, None, None, 120, False)
    assert "no route to any qualifying facility in the dry season" in w
    assert "no route to any qualifying facility in the flood" in w


def test_facility_changes_in_the_flood():
    w = build_warnings(20, 25, 5, 9, 30, 120, False)
    assert "the nearest qualifying facility changes in the flood" in w


def test_flood_adds_a_lot_of_time():
    w = build_warnings(20, 40, 5, 5, 30, 120, False)
    assert any("adds 20 minutes" in x for x in w)


def test_flood_pushes_beyond_target_only_when_dry_was_within_it():
    pushed = build_warnings(100, 130, 5, 5, 140, 120, False)
    assert "the flood pushes this point beyond the target time" in pushed
    already_out = build_warnings(130, 150, 5, 5, 160, 120, False)
    assert "the flood pushes this point beyond the target time" not in already_out
    assert "outside the target time even in the dry season" in already_out


def test_backup_much_slower_needs_both_an_absolute_and_a_relative_gap():
    slow = build_warnings(20, 20, 5, 5, 60, 120, False)
    assert "the backup facility is much slower than the first choice" in slow
    close = build_warnings(20, 20, 5, 5, 35, 120, False)
    assert "the backup facility is much slower than the first choice" not in close


def test_flood_path_crosses_flooded_ground_flag_passes_through():
    w = build_warnings(20, 21, 5, 5, 25, 120, True)
    assert "the flood-season path crosses flooded ground" in w
