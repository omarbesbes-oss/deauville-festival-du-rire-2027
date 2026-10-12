from datetime import datetime
from pathlib import Path

from festival.errors import NotFoundError, ValidationError
from festival.festival import Festival
from festival.models import Artist, Lineup, Performance, Solo, Workshop
from festival.storage import load_festival, save_festival


class FestivalService:
    """Gère les modifications du festival et leur sauvegarde."""

    def __init__(self, path: str):
        self.path = Path(path)

    def load(self) -> Festival:
        return load_festival(str(self.path))

    def _apply(self, action):
        """Charge, modifie, puis sauvegarde si l'action réussit."""
        festival = self.load()

        result = action(festival)

        save_festival(festival, str(self.path))

        return result

    def add_artist(self, artist: Artist) -> None:
        """Ajoute un artiste et sauvegarde le festival."""
        self._apply(lambda festival: festival.add_artist(artist))

    def add_performance(self, data: dict) -> Performance:
        """Construit, valide et sauvegarde une représentation."""

        def create(festival):
            venues = {v.slug: v for v in festival.venues}
            artists = {a.slug: a for a in festival.artists}

            venue_slug = data["venue"]

            if venue_slug not in venues:
                raise NotFoundError(f"Venue '{venue_slug}' does not exist.")

            def find_artist(slug):
                if slug not in artists:
                    raise NotFoundError(f"Artist '{slug}' does not exist.")
                return artists[slug]

            common = {
                "title": data["title"],
                "venue": venues[venue_slug],
                "start": datetime.fromisoformat(data["start"]),
                "duration_minutes": data["duration_minutes"],
                "description": data.get("description", ""),
            }

            kind = data["kind"]

            if kind == "solo":
                show = Solo(
                    **common,
                    artist=find_artist(data["artist"]),
                    min_age=data["min_age"],
                )

            elif kind == "lineup":
                show = Lineup(
                    **common,
                    host=find_artist(data["host"]),
                    acts=[find_artist(slug) for slug in data["acts"]],
                )

            elif kind == "workshop":
                show = Workshop(
                    **common,
                    teacher=find_artist(data["teacher"]),
                    max_participants=data["max_participants"],
                    participants=data.get("participants", []),
                )

            else:
                raise ValidationError(f"Unknown performance kind: {kind}.")

            festival.add_performance(show)

            return show

        return self._apply(create)

    def replace_performance(
        self,
        performance_id: str,
        data: dict,
    ) -> Performance:
        """Remplace un spectacle et sauvegarde le résultat."""

        def replace(festival):
            # Vérifier que le spectacle original existe
            original = next(
                (show for show in festival.performances if show.id == performance_id),
                None,
            )

            if original is None:
                raise NotFoundError(f"Performance {performance_id} does not exist.")

            # Construire les références depuis le festival chargé
            venues = {v.slug: v for v in festival.venues}
            artists = {a.slug: a for a in festival.artists}

            venue_slug = data["venue"]

            if venue_slug not in venues:
                raise NotFoundError(f"Venue {venue_slug} does not exist.")

            def find_artist(slug):
                if slug not in artists:
                    raise NotFoundError(f"Artist {slug} does not exist.")
                return artists[slug]

            common = {
                "title": data["title"],
                "venue": venues[venue_slug],
                "start": datetime.fromisoformat(data["start"]),
                "duration_minutes": data["duration_minutes"],
                "description": data.get("description", ""),
            }

            kind = data["kind"]

            if kind == "solo":
                replacement = Solo(
                    **common,
                    artist=find_artist(data["artist"]),
                    min_age=data["min_age"],
                )

            elif kind == "lineup":
                replacement = Lineup(
                    **common,
                    host=find_artist(data["host"]),
                    acts=[find_artist(slug) for slug in data["acts"]],
                )

            elif kind == "workshop":
                replacement = Workshop(
                    **common,
                    teacher=find_artist(data["teacher"]),
                    max_participants=data["max_participants"],
                    participants=data.get(
                        "participants",
                        list(original.participants)
                        if isinstance(original, Workshop)
                        else [],
                    ),
                )

            else:
                raise ValidationError(f"Unknown performance kind: {kind}.")

            return festival.replace_performance(
                performance_id,
                replacement,
            )

        return self._apply(replace)

    def move_performance(
        self,
        performance_id: str,
        new_start: datetime,
        new_venue_slug: str,
    ) -> Performance:
        """Déplace une représentation et sauvegarde."""
        return self._apply(
            lambda festival: festival.move_performance(
                performance_id,
                new_start,
                new_venue_slug,
            )
        )

    def cancel_performance(self, performance_id: str) -> Performance:
        """Annule une représentation et sauvegarde."""
        return self._apply(lambda festival: festival.cancel_performance(performance_id))

    def register_participant(
        self,
        performance_id: str,
        name: str,
    ) -> Performance:
        """Inscrit un participant et sauvegarde le festival."""

        def register(festival):
            show = next(
                (p for p in festival.performances if p.id == performance_id),
                None,
            )

            if show is None:
                raise NotFoundError(f"Performance {performance_id} does not exist.")

            if not isinstance(show, Workshop):
                raise ValidationError("This performance is not a workshop.")

            show.register(name)

            return show

        return self._apply(register)
