from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from festival.errors import (
    ConflictError,
    NotFoundError,
    StorageError,
    ValidationError,
)
from festival.models import Artist, Lineup, Solo, Workshop
from festival.service import FestivalService

# ==================================================
# CONFIGURATION
# ==================================================

app = FastAPI(title="Deauville Festival du Rire API")

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "festival.json"

PUBLIC_DIR = BASE_DIR / "web" / "public"
ADMIN_DIR = BASE_DIR / "web" / "admin"

service = FestivalService(str(DATA_FILE))


# ==================================================
# GESTION DES ERREURS
# ==================================================


@app.exception_handler(StorageError)
async def storage_error_handler(
    request: Request,
    exc: StorageError,
):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )


# ==================================================
# CONVERSION DES OBJETS EN JSON
# ==================================================


def artist_to_dict(artist):
    return {
        "slug": artist.slug,
        "name": artist.name,
        "bio": artist.bio,
        "photo_url": artist.photo_url,
    }


def performance_to_dict(show):
    """Transforme un spectacle en réponse JSON."""

    if isinstance(show, Solo):
        artists = [show.artist]
        summary = f"With {show.artist.name}"
        capacity = show.venue.capacity

    elif isinstance(show, Lineup):
        artists = [show.host, *show.acts]
        names = ", ".join(act.name for act in show.acts)
        summary = f"Hosted by {show.host.name}, with {names}"
        capacity = show.venue.capacity

    elif isinstance(show, Workshop):
        artists = [show.teacher]
        summary = f"Workshop with {show.teacher.name}"
        capacity = min(
            show.max_participants,
            show.venue.capacity,
        )

    else:
        raise TypeError("Unknown performance type.")

    data = {
        "id": show.id,
        "kind": type(show).__name__.lower(),
        "title": show.title,
        "venue": show.venue.slug,
        "venue_name": show.venue.name,
        "start": show.start.isoformat(timespec="minutes"),
        "end": show.end.isoformat(timespec="minutes"),
        "duration_minutes": show.duration_minutes,
        "festival_day": show.festival_day.isoformat(),
        "description": show.description,
        "summary": summary,
        "capacity": capacity,
        "artists": [
            {
                "slug": artist.slug,
                "name": artist.name,
            }
            for artist in artists
        ],
    }

    if isinstance(show, Solo):
        data["artist"] = show.artist.slug
        data["min_age"] = show.min_age

    elif isinstance(show, Lineup):
        data["host"] = show.host.slug
        data["acts"] = [act.slug for act in show.acts]

    elif isinstance(show, Workshop):
        data["teacher"] = show.teacher.slug
        data["max_participants"] = show.max_participants
        data["participants"] = list(show.participants)
        data["places_left"] = show.available_places

    return data


# ==================================================
# GET /api/festival
# ==================================================


@app.get("/api/festival")
def get_festival():
    festival = service.load()

    days = [
        (festival.first_day + timedelta(days=i)).isoformat()
        for i in range((festival.last_day - festival.first_day).days + 1)
    ]

    return {
        "name": festival.name,
        "first_day": festival.first_day.isoformat(),
        "last_day": festival.last_day.isoformat(),
        "days": days,
    }


# ==================================================
# GET /api/venues
# ==================================================


@app.get("/api/venues")
def get_venues():
    festival = service.load()

    return [
        {
            "slug": venue.slug,
            "name": venue.name,
            "capacity": venue.capacity,
            "address": venue.address,
        }
        for venue in festival.venues
    ]


# ==================================================
# GET /api/artists
# ==================================================


@app.get("/api/artists")
def get_artists():
    festival = service.load()

    return [artist_to_dict(artist) for artist in festival.artists]


# ==================================================
# GET /api/artists/{slug}
# ==================================================


@app.get("/api/artists/{slug}")
def get_artist(slug: str):
    festival = service.load()

    artist = next(
        (artist for artist in festival.artists if artist.slug == slug),
        None,
    )

    if artist is None:
        raise HTTPException(
            status_code=404,
            detail=f"Artist '{slug}' does not exist.",
        )

    performances = [
        performance_to_dict(show)
        for show in festival.performances
        if slug in show.artist_slugs()
    ]

    return {
        **artist_to_dict(artist),
        "performances": performances,
    }


# ==================================================
# GET /api/programme
# ==================================================


@app.get("/api/programme")
def get_programme(
    day: date | None = None,
    venue: str | None = None,
):
    festival = service.load()
    shows = festival.performances

    if day is not None:
        shows = tuple(show for show in shows if show.festival_day == day)

    if venue is not None:
        shows = tuple(show for show in shows if show.venue.slug == venue)

    return [performance_to_dict(show) for show in shows]


# ==================================================
# GET /api/performances/{id}
# ==================================================


@app.get("/api/performances/{performance_id}")
def get_performance(performance_id: str):
    festival = service.load()

    for show in festival.performances:
        if show.id == performance_id:
            return performance_to_dict(show)

    raise HTTPException(
        status_code=404,
        detail=(f"Performance '{performance_id}' does not exist."),
    )


# ==================================================
# GET /api/now
# ==================================================


@app.get("/api/now")
def get_now(at: datetime | None = None):
    """Retourne les spectacles en cours et les 3 prochains."""

    moment = at if at is not None else datetime.now()

    if moment.tzinfo is not None:
        raise HTTPException(
            status_code=422,
            detail=[
                {
                    "type": "value_error",
                    "loc": ["query", "at"],
                    "msg": "Use local time without timezone.",
                    "input": str(at),
                }
            ],
        )

    festival = service.load()

    current = festival.currently_on_stage(moment)
    upcoming = festival.next_performances(
        moment,
        limit=3,
    )

    return {
        "at": moment.isoformat(timespec="minutes"),
        "now_playing": [performance_to_dict(show) for show in current],
        "up_next": [performance_to_dict(show) for show in upcoming],
    }


# ==================================================
# MODELES PYDANTIC POUR L'ADMINISTRATION
# ==================================================


class ArtistCreate(BaseModel):
    name: str
    bio: str = ""
    photo_url: str = ""


class PerformanceCreate(BaseModel):
    kind: Literal["solo", "lineup", "workshop"]

    title: str
    venue: str
    start: datetime
    duration_minutes: int = Field(ge=1, le=360)
    description: str = ""

    # Champs Solo
    artist: str | None = None
    min_age: int | None = Field(
        default=None,
        ge=0,
        le=18,
    )

    # Champs Lineup
    host: str | None = None
    acts: list[str] | None = None

    # Champs Workshop
    teacher: str | None = None
    max_participants: int | None = Field(
        default=None,
        ge=1,
    )


# ==================================================
# POST /api/artists
# ==================================================


@app.post(
    "/api/artists",
    status_code=status.HTTP_201_CREATED,
)
def create_artist(data: ArtistCreate):
    try:
        artist = Artist(
            name=data.name,
            bio=data.bio,
            photo_url=data.photo_url,
        )

        service.add_artist(artist)

        return artist_to_dict(artist)

    except ConflictError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        )

    except (ValidationError, ValueError) as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        )


# ==================================================
# POST /api/performances
# ==================================================


@app.post(
    "/api/performances",
    status_code=status.HTTP_201_CREATED,
)
def create_performance(data: PerformanceCreate):
    """Ajoute une représentation et la sauvegarde."""

    # Les dates sont locales, sans fuseau horaire.
    if data.start.tzinfo is not None:
        raise HTTPException(
            status_code=422,
            detail="Start must be a local date and time.",
        )

    payload = data.model_dump(
        mode="json",
        exclude_none=True,
    )

    # Champs obligatoires selon le type
    required_fields = {
        "solo": ("artist", "min_age"),
        "lineup": ("host", "acts"),
        "workshop": (
            "teacher",
            "max_participants",
        ),
    }

    missing = [field for field in required_fields[data.kind] if field not in payload]

    if missing:
        raise HTTPException(
            status_code=422,
            detail=("Missing fields: " + ", ".join(missing)),
        )

    try:
        show = service.add_performance(payload)

        return performance_to_dict(show)

    except NotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )

    except ConflictError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        )

    except (ValidationError, ValueError) as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        )


@app.put("/api/performances/{performance_id}")
def update_performance(
    performance_id: str,
    data: PerformanceCreate,
):
    """Modifie un spectacle et retourne sa nouvelle version."""

    if data.start.tzinfo is not None:
        raise HTTPException(
            status_code=422,
            detail="Start must be a local date and time.",
        )

    payload = data.model_dump(
        mode="json",
        exclude_none=True,
    )

    required_fields = {
        "solo": ("artist", "min_age"),
        "lineup": ("host", "acts"),
        "workshop": ("teacher", "max_participants"),
    }

    missing = [field for field in required_fields[data.kind] if field not in payload]

    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"Missing fields: {', '.join(missing)}",
        )

    try:
        updated = service.replace_performance(
            performance_id,
            payload,
        )
        return performance_to_dict(updated)

    except NotFoundError as error:
        raise HTTPException(404, detail=str(error))

    except ConflictError as error:
        raise HTTPException(409, detail=str(error))

    except (ValidationError, ValueError) as error:
        raise HTTPException(422, detail=str(error))


# ==================================================
# DELETE /api/performances/{id}
# ==================================================


@app.delete(
    "/api/performances/{performance_id}",
    status_code=204,
)
def delete_performance(performance_id: str):
    """Annule un spectacle et sauvegarde le festival."""

    try:
        service.cancel_performance(performance_id)

        # Le code HTTP 204 ne renvoie pas de contenu.
        return

    except NotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )


# ==================================================
# POST /api/performances/{id}/participants
# ==================================================


class ParticipantCreate(BaseModel):
    name: str


@app.post(
    "/api/performances/{performance_id}/participants",
    status_code=201,
)
def register_participant(
    performance_id: str,
    data: ParticipantCreate,
):
    """Inscrit un participant à un atelier."""

    try:
        workshop = service.register_participant(
            performance_id,
            data.name,
        )

        return performance_to_dict(workshop)

    except NotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )

    except ConflictError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        )

    except (ValidationError, ValueError) as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        )


# ==================================================
# INTERFACES HTML
# Toujours placer les montages à la fin !
# ==================================================

app.mount(
    "/admin",
    StaticFiles(
        directory=ADMIN_DIR,
        html=True,
    ),
    name="admin",
)

app.mount(
    "/",
    StaticFiles(
        directory=PUBLIC_DIR,
        html=True,
    ),
    name="public",
)
