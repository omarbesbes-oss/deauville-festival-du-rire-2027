from festival.storage import load_festival, save_festival

# Charger le fichier original
festival = load_festival("data/festival.json")

# Sauvegarder dans un fichier de test
save_festival(festival, "data/festival_test.json")

print("Sauvegarde effectuée !")

# Recharger le fichier sauvegardé
reloaded = load_festival("data/festival_test.json")

print("Artistes :", len(reloaded.artists))
print("Salles :", len(reloaded.venues))
print("Spectacles :", len(reloaded.performances))

assert len(reloaded.artists) == 12
assert len(reloaded.venues) == 4
assert len(reloaded.performances) == 23

print("Test de rechargement réussi !")
