from datetime import date, datetime

import pytest

from festival.errors import NotFoundError
from festival.festival import Festival
from festival.models import Artist, Solo, Venue


def test_conflicting_show_does_not_change_programme():
    festival = Festival(
        "Test Festival",
        date(2027, 6, 10),
        date(2027, 6, 13),
    )

    venue = Venue("Grand Casino", 650, "Deauville")
    artist = Artist("Hugo Lemaire")

    festival.add_venue(venue)
    festival.add_artist(artist)

    first_show = Solo(
        title="First Show",
        venue=venue,
        start=datetime(2027, 6, 10, 18, 0),
        duration_minutes=60,
        artist=artist,
    )

    festival.add_performance(first_show)

    conflicting_show = Solo(
        title="Conflicting Show",
        venue=venue,
        start=datetime(2027, 6, 10, 18, 30),
        duration_minutes=60,
        artist=artist,
    )

    with pytest.raises(ValueError, match="busy"):
        festival.add_performance(conflicting_show)

    assert len(festival.performances) == 1
    assert festival.performances[0].title == "First Show"


def test_move_conflict_keeps_original():
    festival = Festival(
        "Test Festival",
        date(2027, 6, 10),
        date(2027, 6, 13),
    )

    venue = Venue("Grand Casino", 650, "Deauville")
    artist1 = Artist("Hugo Lemaire")
    artist2 = Artist("Nora Lebrun")

    festival.add_venue(venue)
    festival.add_artist(artist1)
    festival.add_artist(artist2)

    first = Solo(
        "First Show",
        venue,
        datetime(2027, 6, 10, 18, 0),
        60,
        artist1,
    )

    second = Solo(
        "Second Show",
        venue,
        datetime(2027, 6, 10, 21, 0),
        60,
        artist2,
    )

    festival.add_performance(first)
    festival.add_performance(second)

    original_id = second.id

    with pytest.raises(ValueError, match="busy"):
        festival.move_performance(
            original_id,
            datetime(2027, 6, 10, 18, 30),
            venue.slug,
        )

    assert len(festival.performances) == 2
    assert any(show.id == original_id for show in festival.performances)

    assert second.start == datetime(2027, 6, 10, 21, 0)


def test_move_performance_success():
    festival = Festival(
        "Test Festival",
        date(2027, 6, 10),
        date(2027, 6, 13),
    )

    venue = Venue("Grand Casino", 650, "Deauville")
    artist = Artist("Hugo Lemaire")

    festival.add_venue(venue)
    festival.add_artist(artist)

    show = Solo(
        title="Comedy Show",
        venue=venue,
        start=datetime(2027, 6, 10, 18, 0),
        duration_minutes=60,
        artist=artist,
    )

    festival.add_performance(show)

    old_id = show.id
    new_start = datetime(2027, 6, 10, 20, 0)

    moved = festival.move_performance(
        old_id,
        new_start,
        venue.slug,
    )

    assert len(festival.performances) == 1
    assert moved.start == new_start
    assert moved.id != old_id
    assert festival.performances[0].id == moved.id
    assert all(p.id != old_id for p in festival.performances)


def test_cancel_performance():
    festival = Festival(
        "Test Festival",
        date(2027, 6, 10),
        date(2027, 6, 13),
    )

    venue = Venue("Grand Casino", 650, "Deauville")
    artist = Artist("Hugo Lemaire")

    festival.add_venue(venue)
    festival.add_artist(artist)

    show = Solo(
        "Comedy Show",
        venue,
        datetime(2027, 6, 10, 18, 0),
        60,
        artist,
    )

    festival.add_performance(show)

    assert len(festival.performances) == 1

    cancelled = festival.cancel_performance(show.id)

    assert cancelled.title == "Comedy Show"
    assert len(festival.performances) == 0

    with pytest.raises(NotFoundError, match="does not exist"):
        festival.cancel_performance(show.id)
