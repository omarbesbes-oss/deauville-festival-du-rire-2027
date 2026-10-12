# Reads the data of the festival and prints its name.
# Run it from this folder: uv run main.py
#
# The three lines below open the file and turn its JSON text into Python
# dicts and lists. How they work is explained in step 05; for now, use them.

import json
from datetime import date, datetime

from festival.festival import Festival
from festival.models import Artist, Lineup, Solo, Venue, Workshop
from festival.storage import load_festival

with open("data/festival.json", encoding="utf-8") as file:
    festival = json.load(file)

print(festival["name"])

print("\n=== INFORMATIONS DU FESTIVAL ===")

# Afficher les informations générales
print("Nom :", festival["name"])
print("Dates :", festival["first_day"], "au", festival["last_day"])

# Afficher les données disponibles
print("\nClés du fichier JSON :")
print(list(festival.keys()))

# Compter les éléments
print("\nNombre d'artistes :", len(festival["artists"]))
print("Nombre de salles :", len(festival["venues"]))
print("Nombre de représentations :", len(festival["performances"]))

# Observer le premier élément de chaque catégorie
print("\n=== PREMIER ARTISTE ===")
print(festival["artists"][0])

print("\n=== PREMIÈRE SALLE ===")
print(festival["venues"][0])

print("\n=== PREMIÈRE REPRÉSENTATION ===")
print(festival["performances"][0])


print("\n=== TEST CLASSE ARTIST ===")

artist1 = Artist("Hugo Lemaire", "Musical comedy", "")

print("Nom :", artist1.name)
print("Slug :", artist1.slug)
print("Bio :", artist1.bio)

artist2 = Artist("  Élodie  Marchal !  ")

print("\nNom nettoyé :", artist2.name)
print("Slug généré :", artist2.slug)

print("\n=== TEST CLASSE VENUE ===")

# Créer une salle valide
venue1 = Venue("Grand Casino", 650, "Seafront, main hall")

print("Nom :", venue1.name)
print("Slug :", venue1.slug)
print("Capacité :", venue1.capacity)
print("Adresse :", venue1.address)

# Vérifier que les espaces sont nettoyés
venue2 = Venue("  Théâtre des Planches  ", 200, "Centre-ville")

print("\nDeuxième salle :", venue2.name)
print("Slug :", venue2.slug)

# Tester une salle invalide
print("\n=== TEST ERREUR ===")

try:
    venue3 = Venue("Salle invalide", 0, "Deauville")
except ValueError as error:
    print("Erreur détectée :", error)

print("\n=== TEST CLASSE SOLO ===")

solo = Solo(
    title="Hugo Comedy Show",
    venue=venue1,
    start=datetime(2027, 6, 10, 18, 0),
    duration_minutes=60,
    artist=artist1,
    min_age=12,
    description="A musical comedy show.",
)

print("Titre :", solo.title)
print("Salle :", solo.venue.name)
print("Début :", solo.start)
print("Fin :", solo.end)
print("Identifiant :", solo.id)
print("Artistes :", solo.artist_slugs())
print("Age minimum :", solo.min_age)

print("\n=== TEST CLASSE LINEUP ===")

host = Artist("Paul Kerbrat")
act1 = Artist("Nora Lebrun")
act2 = Artist("Max Pellerin")
act3 = Artist("Léa Fontaine")

lineup = Lineup(
    title="Comedy Night",
    venue=venue1,
    start=datetime(2027, 6, 10, 20, 30),
    duration_minutes=90,
    host=host,
    acts=[act1, act2, act3],
    description="An evening of stand-up comedy.",
)

print("Titre :", lineup.title)
print("Salle :", lineup.venue.name)
print("Présentateur :", lineup.host.name)
print("Artistes :", [artist.name for artist in lineup.acts])
print("Début :", lineup.start)
print("Fin :", lineup.end)
print("Identifiant :", lineup.id)

print("\n=== TEST ERREUR LINEUP ===")

try:
    invalid_lineup = Lineup(
        title="Too Short",
        venue=venue1,
        start=datetime(2027, 6, 11, 20, 0),
        duration_minutes=20,
        host=host,
        acts=[act1, act2, act3],
    )
except ValueError as error:
    print("Erreur détectée :", error)

print("\n=== TEST CLASSE WORKSHOP ===")

workshop = Workshop(
    title="Comedy Writing Workshop",
    venue=venue1,
    start=datetime(2027, 6, 11, 14, 0),
    duration_minutes=90,
    teacher=artist1,
    max_participants=2,
    description="Learn how to write comedy.",
)

print("Titre :", workshop.title)
print("Professeur :", workshop.teacher.name)
print("Salle :", workshop.venue.name)
print("Capacité :", workshop.capacity)

# Inscrire deux participants
workshop.register("Camille R.")
workshop.register("Sophie Martin")

print("Inscrits :", workshop.participants)
print("Places restantes :", workshop.available_places)

# Tester une inscription en double
print("\n=== TEST DOUBLON ===")
try:
    workshop.register("camille r.")
except ValueError as error:
    print("Erreur détectée :", error)

# Tester un atelier complet
print("\n=== TEST ATELIER COMPLET ===")
try:
    workshop.register("Lucas Bernard")
except ValueError as error:
    print("Erreur détectée :", error)

print("\n=== TEST CLASSE FESTIVAL ===")

my_festival = Festival(
    "Deauville Festival du Rire 2027",
    date(2027, 6, 10),
    date(2027, 6, 13),
)

# Ajouter les artistes et la salle
my_festival.add_artist(artist1)
my_festival.add_artist(host)
my_festival.add_artist(act1)
my_festival.add_artist(act2)
my_festival.add_artist(act3)
my_festival.add_venue(venue1)

# Ajouter un premier spectacle
my_festival.add_performance(solo)

print("Premier spectacle ajouté :", solo.title)

# Tenter un deuxième spectacle trop proche
conflicting_show = Solo(
    title="Another Hugo Show",
    venue=venue1,
    start=datetime(2027, 6, 10, 18, 30),
    duration_minutes=60,
    artist=artist1,
    min_age=0,
)

try:
    my_festival.add_performance(conflicting_show)
except ValueError as error:
    print("Conflit détecté :", error)

print("\nProgramme enregistré en mémoire :")

for performance in my_festival.performances:
    print(performance.title, "-", performance.start)

print("\n=== CHARGEMENT DU VRAI FESTIVAL ===")

real_festival = load_festival("data/festival.json")

print("Nom :", real_festival.name)
print("Début :", real_festival.first_day)
print("Fin :", real_festival.last_day)

print("\nNombre d'artistes :", len(real_festival.artists))
print("Nombre de salles :", len(real_festival.venues))

print("\n=== ARTISTES DU FESTIVAL ===")
for artist in real_festival.artists:
    print(artist.name, "-", artist.slug)

print("\n=== SALLES DU FESTIVAL ===")
for venue in real_festival.venues:
    print(venue.name, "-", venue.capacity, "places")

print("\n=== CHARGEMENT DES 23 SPECTACLES ===")

print("Nombre de spectacles :", len(real_festival.performances))

for show in real_festival.performances:
    print(
        show.start.strftime("%d/%m/%Y %H:%M"),
        "|",
        show.title,
        "|",
        show.venue.name,
        "|",
        type(show).__name__,
    )

print("\n=== PROGRAMME DU 11 JUIN 2027 ===")

programme = real_festival.programme_for_day(date(2027, 6, 11))

for show in programme:
    print(show.start.strftime("%d/%m %H:%M"), "|", show.title, "|", show.venue.name)

print("\n=== ARTISTES ET NOMBRE DE SPECTACLES ===")

for artist, count in real_festival.artist_show_counts():
    print(f"{artist.name} : {count} spectacle(s)")

print("\nNombre d'artistes :", len(real_festival.artist_show_counts()))

print("\n=== SPECTACLES EN COURS ===")

moment = datetime(2027, 6, 12, 21, 15)

print("Date et heure :", moment)

current_shows = real_festival.currently_on_stage(moment)

for show in current_shows:
    print(
        show.title,
        "|",
        show.venue.name,
        "|",
        show.start.strftime("%H:%M"),
        "-",
        show.end.strftime("%H:%M"),
    )

print("\n=== LES 3 PROCHAINS SPECTACLES ===")

next_shows = real_festival.next_performances(moment)

for show in next_shows:
    print(
        show.start.strftime("%d/%m %H:%M"),
        "|",
        show.title,
        "|",
        show.venue.name,
    )
