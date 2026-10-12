import copy
from datetime import date, datetime, timedelta

from festival.errors import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from festival.models import Artist, Performance, Venue


class Festival:
    """Gère les artistes, les salles et le programme du festival."""

    def __init__(
        self,
        name: str,
        first_day: date,
        last_day: date,
    ):
        if not isinstance(name, str) or not name.strip():
            raise ValidationError("A festival must have a name.")

        if (
            not isinstance(first_day, date)
            or isinstance(first_day, datetime)
            or not isinstance(last_day, date)
            or isinstance(last_day, datetime)
            or first_day > last_day
        ):
            raise ValidationError("Festival dates are invalid.")

        self.name = name.strip()
        self.first_day = first_day
        self.last_day = last_day

        self._artists: dict[str, Artist] = {}
        self._venues: dict[str, Venue] = {}
        self._performances: dict[str, Performance] = {}

    # ==================================================
    # PROPRIETES
    # ==================================================

    @property
    def artists(self) -> tuple[Artist, ...]:
        return tuple(
            sorted(
                self._artists.values(),
                key=lambda artist: artist.slug,
            )
        )

    @property
    def venues(self) -> tuple[Venue, ...]:
        return tuple(self._venues.values())

    @property
    def performances(self) -> tuple[Performance, ...]:
        return tuple(
            sorted(
                self._performances.values(),
                key=lambda show: (
                    show.start,
                    show.venue.name,
                ),
            )
        )

    # ==================================================
    # ARTISTES
    # ==================================================

    def add_artist(self, artist: Artist) -> None:
        """Ajoute un artiste au festival."""

        if not isinstance(artist, Artist):
            raise ValidationError("A valid artist is required.")

        if artist.slug in self._artists:
            raise ConflictError(f"Artist {artist.name} already exists.")

        self._artists[artist.slug] = artist

    # ==================================================
    # SALLES
    # ==================================================

    def add_venue(self, venue: Venue) -> None:
        """Ajoute une salle au festival."""

        if not isinstance(venue, Venue):
            raise ValidationError("A valid venue is required.")

        if venue.slug in self._venues:
            raise ConflictError(f"Venue {venue.name} already exists.")

        self._venues[venue.slug] = venue

    # ==================================================
    # AJOUT D'UN SPECTACLE
    # ==================================================

    def add_performance(
        self,
        performance: Performance,
    ) -> None:
        """Valide et ajoute une représentation."""

        if not isinstance(performance, Performance):
            raise ValidationError("A valid performance is required.")

        # Vérifier la journée du festival.
        # Une journée commence à 06:00 et se termine
        # à 05:59 le lendemain.

        festival_day = (performance.start - timedelta(hours=6)).date()

        if not (self.first_day <= festival_day <= self.last_day):
            raise ConflictError(f"{performance.title} is outside festival dates.")

        # Vérifier que la salle existe.

        if performance.venue.slug not in self._venues:
            raise NotFoundError(f"Venue {performance.venue.slug} does not exist.")

        # Vérifier que tous les artistes existent.

        for slug in performance.artist_slugs():
            if slug not in self._artists:
                raise NotFoundError(f"Artist {slug} does not exist.")

        # Vérifier que l'identifiant est disponible.

        if performance.id in self._performances:
            raise ConflictError(f"Performance {performance.id} already exists.")

        # Une pause de 30 minutes est obligatoire
        # entre deux représentations dans une même salle
        # ou partageant un artiste.

        gap = timedelta(minutes=30)

        for existing in self._performances.values():
            too_close = (
                performance.start < existing.end + gap
                and existing.start < performance.end + gap
            )

            if not too_close:
                continue

            # Conflit de salle

            if performance.venue.slug == existing.venue.slug:
                raise ConflictError(
                    f"{performance.venue.name} is busy with "
                    f"{existing.title} "
                    f"({existing.start:%Y-%m-%d %H:%M}-"
                    f"{existing.end:%H:%M}). "
                    "Leave 30 minutes between two shows."
                )

            # Conflit d'artistes

            shared_artists = set(performance.artist_slugs()) & set(
                existing.artist_slugs()
            )

            if shared_artists:
                raise ConflictError(
                    f"Artist {min(shared_artists)} is busy "
                    f"with {existing.title}. "
                    "Leave 30 minutes between performances."
                )

        # Ajouter uniquement après toutes les validations.

        self._performances[performance.id] = performance

    # ==================================================
    # PROGRAMME PAR JOUR
    # ==================================================

    def programme_for_day(
        self,
        day: date,
    ) -> tuple[Performance, ...]:
        """Retourne le programme d'une journée."""

        if not isinstance(day, date) or isinstance(day, datetime):
            raise ValidationError("A valid festival day is required.")

        if not (self.first_day <= day <= self.last_day):
            raise ValidationError(f"{day} is outside the festival dates.")

        return tuple(show for show in self.performances if show.festival_day == day)

    # ==================================================
    # NOMBRE DE SPECTACLES PAR ARTISTE
    # ==================================================

    def artist_show_counts(
        self,
    ) -> list[tuple[Artist, int]]:
        """Compte les spectacles de chaque artiste."""

        results = []

        for artist in self.artists:
            count = sum(
                artist.slug in show.artist_slugs() for show in self.performances
            )

            results.append((artist, count))

        return results

    # ==================================================
    # SPECTACLES EN COURS
    # ==================================================

    def currently_on_stage(
        self,
        moment: datetime,
    ) -> tuple[Performance, ...]:
        """Retourne les spectacles actuellement en cours."""

        if not isinstance(moment, datetime) or moment.tzinfo is not None:
            raise ValidationError("Use a valid local date and time without timezone.")

        return tuple(
            show for show in self.performances if show.start <= moment < show.end
        )

    # ==================================================
    # PROCHAINS SPECTACLES
    # ==================================================

    def next_performances(
        self,
        moment: datetime,
        limit: int = 3,
    ) -> tuple[Performance, ...]:
        """Retourne les prochaines représentations."""

        if not isinstance(moment, datetime) or moment.tzinfo is not None:
            raise ValidationError("Use a valid local date and time without timezone.")

        if type(limit) is not int or limit < 0:
            raise ValidationError("Limit must be a positive number or zero.")

        upcoming = [show for show in self.performances if show.start > moment]

        return tuple(upcoming[:limit])

    # ==================================================
    # REMPLACEMENT COMPLET D'UN SPECTACLE
    # ==================================================

    def replace_performance(
        self,
        performance_id: str,
        replacement: Performance,
    ) -> Performance:
        """
        Remplace une représentation par une nouvelle version.

        En cas d'échec, l'ancienne version est restaurée.
        """

        if performance_id not in self._performances:
            raise NotFoundError(f"Performance {performance_id} does not exist.")

        if not isinstance(replacement, Performance):
            raise ValidationError("A valid replacement performance is required.")

        original = self._performances[performance_id]

        # Retirer temporairement l'ancienne version.
        del self._performances[performance_id]

        try:
            # Vérifier toutes les règles sur la nouvelle version.
            self.add_performance(replacement)

        except Exception:
            # Restaurer l'original en cas d'erreur.
            self._performances[performance_id] = original
            raise

        return replacement

    # ==================================================
    # DEPLACEMENT D'UN SPECTACLE
    # ==================================================

    def move_performance(
        self,
        performance_id: str,
        new_start: datetime,
        new_venue_slug: str,
    ) -> Performance:
        """
        Déplace un spectacle vers un autre horaire ou une autre salle.

        Toutes les autres informations sont conservées.
        """

        if performance_id not in self._performances:
            raise NotFoundError(f"Performance {performance_id} does not exist.")

        if new_venue_slug not in self._venues:
            raise NotFoundError(f"Venue {new_venue_slug} does not exist.")

        if not isinstance(new_start, datetime) or new_start.tzinfo is not None:
            raise ValidationError("Start must be a local date and time.")

        original = self._performances[performance_id]

        # Copie superficielle : les artistes et les inscriptions
        # restent associés au spectacle.

        candidate = copy.copy(original)
        candidate._start = new_start
        candidate._venue = self._venues[new_venue_slug]

        # Réutiliser la validation et la restauration
        # centralisées dans replace_performance().

        return self.replace_performance(
            performance_id,
            candidate,
        )

    # ==================================================
    # ANNULATION D'UN SPECTACLE
    # ==================================================

    def cancel_performance(
        self,
        performance_id: str,
    ) -> Performance:
        """Supprime une représentation du programme."""

        if performance_id not in self._performances:
            raise NotFoundError(f"Performance {performance_id} does not exist.")

        return self._performances.pop(performance_id)
