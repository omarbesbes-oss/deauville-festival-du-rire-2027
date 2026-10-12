import json
import os
import tempfile
from datetime import date, datetime
from pathlib import Path

from festival.errors import StorageError, ValidationError
from festival.festival import Festival
from festival.models import Artist, Lineup, Solo, Venue, Workshop


def load_festival(path: str) -> Festival:
    """Charge et valide les données du festival depuis un fichier JSON."""

    file_path = Path(path)

    # ==================================================
    # 1. LECTURE DU FICHIER JSON
    # ==================================================

    try:
        with file_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise StorageError(
            f"Unable to read festival file '{file_path}': {error}"
        ) from error

    # ==================================================
    # 2. CONSTRUCTION ET VALIDATION DU FESTIVAL
    # ==================================================

    try:
        festival = Festival(
            name=data["name"],
            first_day=date.fromisoformat(data["first_day"]),
            last_day=date.fromisoformat(data["last_day"]),
        )

        # ----------------------------------------------
        # Chargement des artistes
        # ----------------------------------------------

        for artist_data in data["artists"]:
            artist = Artist(
                name=artist_data["name"],
                bio=artist_data.get("bio", ""),
                photo_url=artist_data.get("photo_url", ""),
            )

            festival.add_artist(artist)

        # ----------------------------------------------
        # Chargement des salles
        # ----------------------------------------------

        for venue_data in data["venues"]:
            venue = Venue(
                name=venue_data["name"],
                capacity=venue_data["capacity"],
                address=venue_data["address"],
            )

            festival.add_venue(venue)

        # ----------------------------------------------
        # Dictionnaires de correspondance
        # ----------------------------------------------

        artists_by_slug = {artist.slug: artist for artist in festival.artists}

        venues_by_slug = {venue.slug: venue for venue in festival.venues}

        # ----------------------------------------------
        # Chargement des représentations
        # ----------------------------------------------

        for show_data in data["performances"]:
            kind = show_data["kind"]
            title = show_data["title"]
            venue_slug = show_data["venue"]

            # Vérifier que la salle existe
            if venue_slug not in venues_by_slug:
                raise ValidationError(f"Unknown venue '{venue_slug}' for {title}.")

            venue = venues_by_slug[venue_slug]

            # IMPORTANT :
            # title=title fixe la valeur pour cette
            # représentation et corrige Ruff B023.
            def get_artist(
                slug: str,
                title: str = title,
            ) -> Artist:
                if slug not in artists_by_slug:
                    raise ValidationError(f"Unknown artist '{slug}' for {title}.")

                return artists_by_slug[slug]

            # Champs communs aux spectacles
            common = {
                "title": title,
                "venue": venue,
                "start": datetime.fromisoformat(show_data["start"]),
                "duration_minutes": show_data["duration_minutes"],
                "description": show_data.get(
                    "description",
                    "",
                ),
            }

            # ------------------------------------------
            # Solo
            # ------------------------------------------

            if kind == "solo":
                performance = Solo(
                    **common,
                    artist=get_artist(show_data["artist"]),
                    min_age=show_data["min_age"],
                )

            # ------------------------------------------
            # Lineup
            # ------------------------------------------

            elif kind == "lineup":
                performance = Lineup(
                    **common,
                    host=get_artist(show_data["host"]),
                    acts=[get_artist(slug) for slug in show_data["acts"]],
                )

            # ------------------------------------------
            # Workshop
            # ------------------------------------------

            elif kind == "workshop":
                performance = Workshop(
                    **common,
                    teacher=get_artist(show_data["teacher"]),
                    max_participants=show_data["max_participants"],
                    participants=show_data.get(
                        "participants",
                        [],
                    ),
                )

            else:
                raise ValidationError(f"Unknown performance kind '{kind}' for {title}.")

            # Vérifier les références, les dates,
            # les identifiants et les conflits horaires.
            festival.add_performance(performance)

        return festival

    except (
        KeyError,
        TypeError,
        ValueError,
        IndexError,
    ) as error:
        raise StorageError(
            f"Invalid festival data in '{file_path}': {error}"
        ) from error


def save_festival(
    festival: Festival,
    path: str,
) -> None:
    """Sauvegarde le festival dans un fichier JSON atomiquement."""

    # ==================================================
    # 1. PREPARER LES DONNEES
    # ==================================================

    data = {
        "name": festival.name,
        "first_day": festival.first_day.isoformat(),
        "last_day": festival.last_day.isoformat(),
        "venues": [],
        "artists": [],
        "performances": [],
    }

    # ----------------------------------------------
    # Sauvegarder les salles
    # ----------------------------------------------

    for venue in festival.venues:
        data["venues"].append(
            {
                "name": venue.name,
                "capacity": venue.capacity,
                "address": venue.address,
            }
        )

    # ----------------------------------------------
    # Sauvegarder les artistes
    # ----------------------------------------------

    for artist in festival.artists:
        data["artists"].append(
            {
                "name": artist.name,
                "bio": artist.bio,
                "photo_url": artist.photo_url,
            }
        )

    # ----------------------------------------------
    # Sauvegarder les représentations
    # ----------------------------------------------

    for show in festival.performances:
        show_data = {
            "kind": type(show).__name__.lower(),
            "title": show.title,
            "venue": show.venue.slug,
            "start": show.start.isoformat(timespec="minutes"),
            "duration_minutes": show.duration_minutes,
            "description": show.description,
        }

        if isinstance(show, Solo):
            show_data["artist"] = show.artist.slug
            show_data["min_age"] = show.min_age

        elif isinstance(show, Lineup):
            show_data["host"] = show.host.slug
            show_data["acts"] = [artist.slug for artist in show.acts]

        elif isinstance(show, Workshop):
            show_data["teacher"] = show.teacher.slug
            show_data["max_participants"] = show.max_participants
            show_data["participants"] = list(show.participants)

        else:
            raise StorageError(f"Unsupported performance type: {type(show).__name__}")

        data["performances"].append(show_data)

    # ==================================================
    # 2. SAUVEGARDE SECURISEE
    # ==================================================

    destination = Path(path)
    temporary_path = None

    try:
        # Ecrire dans un fichier temporaire
        # situé dans le même dossier que la destination.
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=destination.parent,
            prefix=".festival_",
            suffix=".tmp",
            delete=False,
        ) as file:
            temporary_path = Path(file.name)

            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2,
            )

            file.write("\n")

            # Forcer l'écriture sur le disque.
            file.flush()
            os.fsync(file.fileno())

        # Remplacer le fichier uniquement
        # lorsque l'écriture est terminée.
        os.replace(
            temporary_path,
            destination,
        )

    except (
        OSError,
        TypeError,
        ValueError,
    ) as error:
        raise StorageError(
            f"Unable to save festival to '{destination}': {error}"
        ) from error

    finally:
        # Supprimer le temporaire s'il existe encore.
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass
