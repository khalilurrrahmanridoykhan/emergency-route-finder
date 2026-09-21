"""De-duplication of OSM facility features."""
from prepare_accessmod_inputs import same_facility


def test_unnamed_node_beside_a_named_one_is_a_duplicate():
    assert same_facility("sunamganj general hospital", "", 40)
    assert same_facility("", "", 100)


def test_spelling_variants_close_together_are_duplicates():
    assert same_facility("bishwamvarpur upazila health complex", "bishwamvpur upazila health complex", 90)


def test_different_hospitals_next_to_each_other_are_kept():
    # Habiganj General Hospital and Habiganj Medical College are about 100 m apart in OSM.
    assert not same_facility("habiganj general hospital", "habiganj medical college", 100)


def test_same_name_within_1500m_is_one_facility_but_not_farther():
    name = "m.a.g osmani medical college hospital"
    assert same_facility(name, name, 1200)
    assert not same_facility("community clinic", "community clinic", 3000)
