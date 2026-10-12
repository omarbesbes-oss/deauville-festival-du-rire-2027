from fastapi.testclient import TestClient

from api import app
from festival.service import FestivalService
from festival.storage import load_festival, save_festival

client = TestClient(app)


# -----------------------------------------
# TEST 1 : Informations du festival
# -----------------------------------------


def test_festival():
    response = client.get("/api/festival")

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Deauville Festival du Rire 2027"
    assert data["first_day"] == "2027-06-10"
    assert data["last_day"] == "2027-06-13"
    assert len(data["days"]) == 4


# -----------------------------------------
# TEST 2 : Liste des salles
# -----------------------------------------


def test_venues():
    response = client.get("/api/venues")

    assert response.status_code == 200
    assert len(response.json()) == 4


# -----------------------------------------
# TEST 3 : Liste des artistes
# -----------------------------------------


def test_artists():
    response = client.get("/api/artists")

    assert response.status_code == 200
    assert len(response.json()) == 12


# -----------------------------------------
# TEST 4 : Consulter un artiste
# -----------------------------------------


def test_get_artist():
    response = client.get("/api/artists/hugo-lemaire")

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Hugo Lemaire"
    assert data["slug"] == "hugo-lemaire"
    assert len(data["performances"]) == 4


# -----------------------------------------
# TEST 5 : Artiste inexistant
# -----------------------------------------


def test_get_unknown_artist():
    response = client.get("/api/artists/unknown-artist")

    assert response.status_code == 404
    assert "detail" in response.json()


# -----------------------------------------
# TEST 6 : Programme complet
# -----------------------------------------


def test_programme():
    response = client.get("/api/programme")

    assert response.status_code == 200
    assert len(response.json()) == 23


# -----------------------------------------
# TEST 7 : Programme par journée
# -----------------------------------------


def test_programme_day():
    response = client.get(
        "/api/programme",
        params={"day": "2027-06-11"},
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 7

    assert all(show["festival_day"] == "2027-06-11" for show in data)


# -----------------------------------------
# TEST 8 : Programme par salle
# -----------------------------------------


def test_programme_venue():
    response = client.get(
        "/api/programme",
        params={"venue": "le-kiosque"},
    )

    assert response.status_code == 200

    assert all(show["venue"] == "le-kiosque" for show in response.json())


# -----------------------------------------
# TEST 9 : Consulter un spectacle
# -----------------------------------------


def test_get_performance():
    response = client.get("/api/performances/grand-casino-2027-06-10-2030")

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "Opening Gala"
    assert data["kind"] == "lineup"
    assert data["venue"] == "grand-casino"


# -----------------------------------------
# TEST 10 : Spectacle inexistant
# -----------------------------------------


def test_get_unknown_performance():
    response = client.get("/api/performances/unknown-performance")

    assert response.status_code == 404
    assert "detail" in response.json()


# -----------------------------------------
# TEST 11 : Spectacles en cours
# -----------------------------------------


def test_now():
    response = client.get(
        "/api/now",
        params={"at": "2027-06-12T21:15"},
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["now_playing"]) == 2
    assert len(data["up_next"]) == 3

    titles = [show["title"] for show in data["now_playing"]]

    assert "Nothing Serious" in titles
    assert "Deauville Comedy Club" in titles


# -----------------------------------------
# TEST 12 : Date invalide
# -----------------------------------------


def test_invalid_day():
    response = client.get(
        "/api/programme",
        params={"day": "not-a-date"},
    )

    assert response.status_code == 422
    assert isinstance(response.json()["detail"], list)


def test_create_artist(tmp_path, monkeypatch):
    test_file = tmp_path / "festival.json"

    festival = load_festival("data/festival.json")
    save_festival(festival, str(test_file))

    monkeypatch.setattr(
        "api.service",
        FestivalService(str(test_file)),
    )

    response = client.post(
        "/api/artists",
        json={
            "name": "  Alice Martin  ",
            "bio": "Stand-up comedian",
            "photo_url": "",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Alice Martin"
    assert data["slug"] == "alice-martin"

    reloaded = load_festival(str(test_file))

    assert len(reloaded.artists) == 13
    assert any(artist.slug == "alice-martin" for artist in reloaded.artists)


def test_create_duplicate_artist(tmp_path, monkeypatch):
    test_file = tmp_path / "festival.json"

    festival = load_festival("data/festival.json")
    save_festival(festival, str(test_file))

    monkeypatch.setattr(
        "api.service",
        FestivalService(str(test_file)),
    )

    response = client.post(
        "/api/artists",
        json={"name": "Hugo Lemaire"},
    )

    assert response.status_code == 409

    reloaded = load_festival(str(test_file))
    assert len(reloaded.artists) == 12


def test_create_solo(tmp_path, monkeypatch):
    test_file = tmp_path / "festival.json"

    original = load_festival("data/festival.json")
    save_festival(original, str(test_file))

    monkeypatch.setattr(
        "api.service",
        FestivalService(str(test_file)),
    )

    response = client.post(
        "/api/performances",
        json={
            "kind": "solo",
            "title": "New Comedy Show",
            "venue": "grand-casino",
            "start": "2027-06-11T12:00",
            "duration_minutes": 60,
            "artist": "hugo-lemaire",
            "min_age": 12,
        },
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["title"] == "New Comedy Show"
    assert data["kind"] == "solo"

    reloaded = load_festival(str(test_file))

    assert len(reloaded.performances) == 24


def test_create_lineup(tmp_path, monkeypatch):
    test_file = tmp_path / "festival.json"

    original = load_festival("data/festival.json")
    save_festival(original, str(test_file))

    monkeypatch.setattr(
        "api.service",
        FestivalService(str(test_file)),
    )

    response = client.post(
        "/api/performances",
        json={
            "kind": "lineup",
            "title": "New Comedy Gala",
            "venue": "grand-casino",
            "start": "2027-06-10T10:00",
            "duration_minutes": 90,
            "host": "paul-kerbrat",
            "acts": ["nora-lebrun", "max-pellerin"],
        },
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["kind"] == "lineup"
    assert data["title"] == "New Comedy Gala"
    assert len(data["acts"]) == 2

    reloaded = load_festival(str(test_file))
    assert len(reloaded.performances) == 24


def test_create_workshop(tmp_path, monkeypatch):
    test_file = tmp_path / "festival.json"

    original = load_festival("data/festival.json")
    save_festival(original, str(test_file))

    monkeypatch.setattr(
        "api.service",
        FestivalService(str(test_file)),
    )

    response = client.post(
        "/api/performances",
        json={
            "kind": "workshop",
            "title": "New Comedy Workshop",
            "venue": "le-kiosque",
            "start": "2027-06-10T10:00",
            "duration_minutes": 60,
            "teacher": "hugo-lemaire",
            "max_participants": 15,
        },
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["kind"] == "workshop"
    assert data["max_participants"] == 15
    assert data["places_left"] == 15

    reloaded = load_festival(str(test_file))
    assert len(reloaded.performances) == 24


def test_update_performance(tmp_path, monkeypatch):
    test_file = tmp_path / "festival.json"

    original = load_festival("data/festival.json")
    save_festival(original, str(test_file))

    monkeypatch.setattr(
        "api.service",
        FestivalService(str(test_file)),
    )

    old_id = "grand-casino-2027-06-10-2030"

    response = client.put(
        f"/api/performances/{old_id}",
        json={
            "kind": "lineup",
            "title": "Opening Gala Updated",
            "venue": "grand-casino",
            "start": "2027-06-10T20:30",
            "duration_minutes": 90,
            "host": "paul-kerbrat",
            "acts": ["nora-lebrun", "max-pellerin"],
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["title"] == "Opening Gala Updated"

    saved = load_festival(str(test_file))
    assert len(saved.performances) == 23


def test_update_unknown_performance(tmp_path, monkeypatch):
    test_file = tmp_path / "festival.json"

    original = load_festival("data/festival.json")
    save_festival(original, str(test_file))

    monkeypatch.setattr(
        "api.service",
        FestivalService(str(test_file)),
    )

    response = client.put(
        "/api/performances/unknown-id",
        json={
            "kind": "solo",
            "title": "Unknown",
            "venue": "grand-casino",
            "start": "2027-06-11T12:00",
            "duration_minutes": 60,
            "artist": "hugo-lemaire",
            "min_age": 12,
        },
    )

    assert response.status_code == 404


def test_delete_performance(tmp_path, monkeypatch):
    test_file = tmp_path / "festival.json"

    original = load_festival("data/festival.json")
    save_festival(original, str(test_file))

    monkeypatch.setattr(
        "api.service",
        FestivalService(str(test_file)),
    )

    performance_id = "grand-casino-2027-06-10-2030"

    response = client.delete(f"/api/performances/{performance_id}")

    assert response.status_code == 204
    assert response.content == b""

    saved = load_festival(str(test_file))

    assert len(saved.performances) == 22

    assert all(show.id != performance_id for show in saved.performances)


def test_delete_unknown_performance(tmp_path, monkeypatch):
    test_file = tmp_path / "festival.json"

    original = load_festival("data/festival.json")
    save_festival(original, str(test_file))

    monkeypatch.setattr(
        "api.service",
        FestivalService(str(test_file)),
    )

    response = client.delete("/api/performances/unknown-id")

    assert response.status_code == 404

    saved = load_festival(str(test_file))

    assert len(saved.performances) == 23


def test_register_participant(tmp_path, monkeypatch):
    test_file = tmp_path / "festival.json"

    original = load_festival("data/festival.json")
    save_festival(original, str(test_file))

    monkeypatch.setattr(
        "api.service",
        FestivalService(str(test_file)),
    )

    workshop = next(
        show
        for show in original.performances
        if show.__class__.__name__ == "Workshop" and show.available_places > 0
    )

    before = len(workshop.participants)

    response = client.post(
        f"/api/performances/{workshop.id}/participants",
        json={"name": "Test Participant"},
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert "Test Participant" in data["participants"]
    assert data["places_left"] == workshop.available_places - 1

    saved = load_festival(str(test_file))
    updated = next(show for show in saved.performances if show.id == workshop.id)

    assert len(updated.participants) == before + 1


def test_register_unknown_performance(tmp_path, monkeypatch):
    test_file = tmp_path / "festival.json"

    original = load_festival("data/festival.json")
    save_festival(original, str(test_file))

    monkeypatch.setattr(
        "api.service",
        FestivalService(str(test_file)),
    )

    response = client.post(
        "/api/performances/unknown-id/participants",
        json={"name": "Test Participant"},
    )

    assert response.status_code == 404


def test_register_on_solo(tmp_path, monkeypatch):
    test_file = tmp_path / "festival.json"

    original = load_festival("data/festival.json")
    save_festival(original, str(test_file))

    monkeypatch.setattr(
        "api.service",
        FestivalService(str(test_file)),
    )

    solo = next(
        show for show in original.performances if show.__class__.__name__ == "Solo"
    )

    response = client.post(
        f"/api/performances/{solo.id}/participants",
        json={"name": "Test Participant"},
    )

    assert response.status_code == 422


def test_register_duplicate_participant(tmp_path, monkeypatch):
    test_file = tmp_path / "festival.json"

    original = load_festival("data/festival.json")
    save_festival(original, str(test_file))

    monkeypatch.setattr(
        "api.service",
        FestivalService(str(test_file)),
    )

    workshop = next(
        show
        for show in original.performances
        if show.__class__.__name__ == "Workshop" and show.available_places >= 2
    )

    url = f"/api/performances/{workshop.id}/participants"

    first = client.post(
        url,
        json={"name": "Alice Test"},
    )

    assert first.status_code == 201, first.text

    second = client.post(
        url,
        json={"name": "alice test"},
    )

    # Une deuxième inscription doit être refusée.
    assert second.status_code == 409, second.text

    saved = load_festival(str(test_file))

    updated = next(show for show in saved.performances if show.id == workshop.id)

    assert sum(name.casefold() == "alice test" for name in updated.participants) == 1


def test_register_full_workshop(tmp_path, monkeypatch):
    test_file = tmp_path / "festival.json"

    original = load_festival("data/festival.json")
    save_festival(original, str(test_file))

    monkeypatch.setattr(
        "api.service",
        FestivalService(str(test_file)),
    )

    workshop = next(
        show
        for show in original.performances
        if show.__class__.__name__ == "Workshop" and show.available_places > 0
    )

    url = f"/api/performances/{workshop.id}/participants"

    # Remplir toutes les places disponibles
    for i in range(workshop.available_places):
        response = client.post(
            url,
            json={"name": f"Participant Test {i}"},
        )
        assert response.status_code == 201, response.text

    # Essayer d'inscrire une personne supplémentaire
    response = client.post(
        url,
        json={"name": "Participant Supplementaire"},
    )

    assert response.status_code == 409, response.text

    # Vérifier que le fichier JSON n'a pas accepté
    # l'inscription supplémentaire
    saved = load_festival(str(test_file))

    updated = next(show for show in saved.performances if show.id == workshop.id)

    assert updated.available_places == 0
    assert "Participant Supplementaire" not in updated.participants


def test_update_performance_conflict(tmp_path, monkeypatch):
    test_file = tmp_path / "festival.json"

    original = load_festival("data/festival.json")
    save_festival(original, str(test_file))

    monkeypatch.setattr(
        "api.service",
        FestivalService(str(test_file)),
    )

    # Choisir deux spectacles existants.
    shows = list(original.performances)

    first = shows[0]
    second = next(show for show in shows if show.id != first.id)

    # Préparer le corps complet de la modification.
    # On essaie de placer le deuxième spectacle
    # exactement dans la salle et à l'heure du premier.
    payload = {
        "kind": second.__class__.__name__.lower(),
        "title": second.title,
        "venue": first.venue.slug,
        "start": first.start.isoformat(timespec="minutes"),
        "duration_minutes": second.duration_minutes,
        "description": second.description,
    }

    from festival.models import Lineup, Solo, Workshop

    if isinstance(second, Solo):
        payload["artist"] = second.artist.slug
        payload["min_age"] = second.min_age

    elif isinstance(second, Lineup):
        payload["host"] = second.host.slug
        payload["acts"] = [a.slug for a in second.acts]

    elif isinstance(second, Workshop):
        payload["teacher"] = second.teacher.slug
        payload["max_participants"] = second.max_participants

    # Vérifier le fichier avant modification.
    before = test_file.read_bytes()

    response = client.put(
        f"/api/performances/{second.id}",
        json=payload,
    )

    # La salle est déjà occupée.
    assert response.status_code == 409, response.text

    # Une modification refusée ne doit pas
    # réécrire ou modifier le fichier.
    after = test_file.read_bytes()

    assert before == after

    # Le programme doit conserver ses 23 spectacles.
    saved = load_festival(str(test_file))

    assert len(saved.performances) == 23
    assert any(show.id == second.id for show in saved.performances)


def test_update_performance_new_id(tmp_path, monkeypatch):
    test_file = tmp_path / "festival.json"

    original = load_festival("data/festival.json")
    save_festival(original, str(test_file))

    monkeypatch.setattr(
        "api.service",
        FestivalService(str(test_file)),
    )

    old_id = "grand-casino-2027-06-10-2030"

    # Modification de l'horaire d'Opening Gala
    response = client.put(
        f"/api/performances/{old_id}",
        json={
            "kind": "lineup",
            "title": "Opening Gala",
            "venue": "grand-casino",
            "start": "2027-06-10T19:00",
            "duration_minutes": 90,
            "host": "paul-kerbrat",
            "acts": [
                "nora-lebrun",
                "max-pellerin",
            ],
        },
    )

    assert response.status_code == 200, response.text

    data = response.json()
    new_id = data["id"]

    assert new_id == "grand-casino-2027-06-10-1900"
    assert new_id != old_id

    # Vérifier le fichier sauvegardé
    saved = load_festival(str(test_file))

    assert len(saved.performances) == 23

    ids = [show.id for show in saved.performances]

    assert new_id in ids
    assert old_id not in ids

    # Vérifier que l'API retrouve le spectacle déplacé
    check = client.get(f"/api/performances/{new_id}")

    assert check.status_code == 200
    assert check.json()["start"] == "2027-06-10T19:00"
