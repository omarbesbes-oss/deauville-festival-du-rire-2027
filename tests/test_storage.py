from festival.storage import load_festival, save_festival


def test_cancel_and_save(tmp_path):
    # Utiliser une copie pour protéger le JSON original
    test_file = tmp_path / "festival.json"

    festival = load_festival("data/festival.json")

    # Vérifier les 23 spectacles initiaux
    assert len(festival.performances) == 23

    # Annuler le premier spectacle
    show = festival.performances[0]
    festival.cancel_performance(show.id)

    assert len(festival.performances) == 22

    # Sauvegarder le programme modifié
    save_festival(festival, str(test_file))

    # Recharger les données sauvegardées
    reloaded = load_festival(str(test_file))

    assert len(reloaded.performances) == 22

    # Vérifier que le spectacle annulé n'existe plus
    assert all(performance.id != show.id for performance in reloaded.performances)
