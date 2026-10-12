from festival.service import FestivalService
from festival.storage import load_festival, save_festival


def test_cancel_is_saved_automatically(tmp_path):
    test_file = tmp_path / "festival.json"

    # Préparer une copie du festival initial
    original = load_festival("data/festival.json")
    save_festival(original, str(test_file))

    service = FestivalService(str(test_file))

    # Vérifier les 23 spectacles initiaux
    festival = service.load()
    assert len(festival.performances) == 23

    # Annuler le premier spectacle
    show_id = festival.performances[0].id
    service.cancel_performance(show_id)

    # Recharger directement depuis le fichier JSON
    reloaded = load_festival(str(test_file))

    assert len(reloaded.performances) == 22
    assert all(show.id != show_id for show in reloaded.performances)
