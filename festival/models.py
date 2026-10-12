import re
import unicodedata
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

from festival.errors import ConflictError, ValidationError

# ==================================================
# GENERATION DES SLUGS
# ==================================================


def make_slug(name: str) -> str:
    """Convertit un nom en identifiant normalisé."""

    if not isinstance(name, str):
        raise ValidationError("A name must be a string.")

    normalized = unicodedata.normalize("NFKD", name)

    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")

    return re.sub(
        r"[^a-z0-9]+",
        "-",
        ascii_name.lower(),
    ).strip("-")


# ==================================================
# ARTIST
# ==================================================


class Artist:
    def __init__(
        self,
        name: str,
        bio: str = "",
        photo_url: str = "",
    ):
        if not isinstance(name, str) or not name.strip():
            raise ValidationError("An artist must have a name.")

        if not isinstance(bio, str):
            raise ValidationError("Artist biography must be a string.")

        if not isinstance(photo_url, str):
            raise ValidationError("Artist photo URL must be a string.")

        clean_name = name.strip()
        slug = make_slug(clean_name)

        if not slug:
            raise ValidationError("An artist name must contain letters or digits.")

        self._name = clean_name
        self._slug = slug
        self.bio = bio
        self.photo_url = photo_url

    @property
    def name(self) -> str:
        return self._name

    @property
    def slug(self) -> str:
        return self._slug

    def __repr__(self) -> str:
        return f"Artist(name={self.name!r}, slug={self.slug!r})"


# ==================================================
# VENUE
# ==================================================


class Venue:
    def __init__(
        self,
        name: str,
        capacity: int,
        address: str,
    ):
        if not isinstance(name, str) or not name.strip():
            raise ValidationError("A venue must have a name.")

        if type(capacity) is not int or capacity < 1:
            raise ValidationError("A venue must have at least one seat.")

        if not isinstance(address, str):
            raise ValidationError("A venue address must be a string.")

        clean_name = name.strip()
        slug = make_slug(clean_name)

        if not slug:
            raise ValidationError("A venue name must contain letters or digits.")

        self._name = clean_name
        self._slug = slug
        self._capacity = capacity
        self._address = address.strip()

    @property
    def name(self) -> str:
        return self._name

    @property
    def slug(self) -> str:
        return self._slug

    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def address(self) -> str:
        return self._address

    def __repr__(self) -> str:
        return (
            f"Venue(name={self.name!r}, capacity={self.capacity}, slug={self.slug!r})"
        )


# ==================================================
# PERFORMANCE : CLASSE ABSTRAITE
# ==================================================


class Performance(ABC):
    def __init__(
        self,
        title: str,
        venue: Venue,
        start: datetime,
        duration_minutes: int,
        description: str = "",
    ):
        if not isinstance(title, str) or not title.strip():
            raise ValidationError("A performance must have a title.")

        if not isinstance(venue, Venue):
            raise ValidationError("A performance needs a valid venue.")

        if not isinstance(start, datetime) or start.tzinfo is not None:
            raise ValidationError("Start must be a local date and time.")

        if type(duration_minutes) is not int or not 1 <= duration_minutes <= 360:
            raise ValidationError("Duration must be between 1 and 360 minutes.")

        if not isinstance(description, str):
            raise ValidationError("Description must be a string.")

        self._title = title.strip()
        self._venue = venue
        self._start = start
        self._duration_minutes = duration_minutes
        self.description = description

    @property
    def title(self) -> str:
        return self._title

    @property
    def venue(self) -> Venue:
        return self._venue

    @property
    def start(self) -> datetime:
        return self._start

    @property
    def duration_minutes(self) -> int:
        return self._duration_minutes

    @property
    def end(self) -> datetime:
        return self.start + timedelta(minutes=self.duration_minutes)

    @property
    def festival_day(self):
        """
        Retourne la journée du festival.

        Une journée commence à 06:00 et se termine
        à 05:59 le lendemain.
        """
        return (self.start - timedelta(hours=6)).date()

    @property
    def id(self) -> str:
        return f"{self.venue.slug}-{self.start:%Y-%m-%d-%H%M}"

    @abstractmethod
    def artist_slugs(self) -> list[str]:
        """Retourne les slugs des artistes mobilisés."""


# ==================================================
# SOLO
# ==================================================


class Solo(Performance):
    def __init__(
        self,
        title: str,
        venue: Venue,
        start: datetime,
        duration_minutes: int,
        artist: Artist,
        min_age: int = 0,
        description: str = "",
    ):
        super().__init__(
            title=title,
            venue=venue,
            start=start,
            duration_minutes=duration_minutes,
            description=description,
        )

        if not isinstance(artist, Artist):
            raise ValidationError("A solo show needs a valid artist.")

        if type(min_age) is not int or not 0 <= min_age <= 18:
            raise ValidationError("Minimum age must be between 0 and 18.")

        self.artist = artist
        self.min_age = min_age

    def artist_slugs(self) -> list[str]:
        return [self.artist.slug]


# ==================================================
# LINEUP
# ==================================================


class Lineup(Performance):
    def __init__(
        self,
        title: str,
        venue: Venue,
        start: datetime,
        duration_minutes: int,
        host: Artist,
        acts: list[Artist],
        description: str = "",
    ):
        super().__init__(
            title=title,
            venue=venue,
            start=start,
            duration_minutes=duration_minutes,
            description=description,
        )

        if not isinstance(host, Artist):
            raise ValidationError("A lineup needs a valid host.")

        if not isinstance(acts, list) or len(acts) < 2:
            raise ValidationError("A lineup needs at least 2 acts.")

        if not all(isinstance(act, Artist) for act in acts):
            raise ValidationError("Every act must be a valid artist.")

        act_slugs = [act.slug for act in acts]

        if len(act_slugs) != len(set(act_slugs)):
            raise ValidationError("An artist cannot appear twice in a lineup.")

        if host.slug in act_slugs:
            raise ValidationError("The host cannot also be an act.")

        # Chaque artiste joue au moins 10 minutes.
        # Il faut 3 minutes entre deux passages.

        minimum_duration = len(acts) * 10 + (len(acts) - 1) * 3

        if duration_minutes < minimum_duration:
            raise ValidationError(
                f"A lineup with {len(acts)} acts needs "
                f"at least {minimum_duration} minutes."
            )

        self.host = host
        self.acts = tuple(acts)

    def artist_slugs(self) -> list[str]:
        return [
            self.host.slug,
            *[act.slug for act in self.acts],
        ]


# ==================================================
# WORKSHOP
# ==================================================


class Workshop(Performance):
    def __init__(
        self,
        title: str,
        venue: Venue,
        start: datetime,
        duration_minutes: int,
        teacher: Artist,
        max_participants: int,
        participants: list[str] | None = None,
        description: str = "",
    ):
        super().__init__(
            title=title,
            venue=venue,
            start=start,
            duration_minutes=duration_minutes,
            description=description,
        )

        if not isinstance(teacher, Artist):
            raise ValidationError("A workshop needs a valid teacher.")

        if type(max_participants) is not int or max_participants < 1:
            raise ValidationError("A workshop must allow at least one participant.")

        if participants is not None and not isinstance(participants, list):
            raise ValidationError("Participants must be a list.")

        self.teacher = teacher
        self._max_participants = max_participants
        self._participants: list[str] = []

        # Réutiliser les contrôles d'inscription.
        for participant in participants or []:
            self.register(participant)

    @property
    def max_participants(self) -> int:
        return self._max_participants

    @property
    def capacity(self) -> int:
        """
        Capacité réelle : la plus petite valeur
        entre la limite de l'atelier et celle de la salle.
        """
        return min(
            self.max_participants,
            self.venue.capacity,
        )

    @property
    def participants(self) -> tuple[str, ...]:
        return tuple(self._participants)

    @property
    def available_places(self) -> int:
        return self.capacity - len(self._participants)

    def register(self, name: str) -> None:
        """Inscrit un participant à l'atelier."""

        # ------------------------------------------
        # 1. Vérification du nom : erreur 422
        # ------------------------------------------

        if not isinstance(name, str) or not name.strip():
            raise ValidationError("A participant must have a name.")

        clean_name = name.strip()

        # ------------------------------------------
        # 2. Doublon : conflit 409
        # ------------------------------------------

        if any(
            participant.casefold() == clean_name.casefold()
            for participant in self._participants
        ):
            raise ConflictError(f"{clean_name} is already registered.")

        # ------------------------------------------
        # 3. Atelier complet : conflit 409
        # ------------------------------------------

        if len(self._participants) >= self.capacity:
            raise ConflictError("This workshop is full.")

        # ------------------------------------------
        # 4. Enregistrement
        # ------------------------------------------

        self._participants.append(clean_name)

    def artist_slugs(self) -> list[str]:
        return [self.teacher.slug]
