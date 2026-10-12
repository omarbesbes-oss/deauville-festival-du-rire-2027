class FestivalError(Exception):
    """Erreur générale liée aux règles du festival."""


class ValidationError(FestivalError, ValueError):
    """Une donnée est invalide : nom, durée, âge, etc."""


class NotFoundError(FestivalError):
    """Un artiste, une salle ou un spectacle est introuvable."""


class ConflictError(FestivalError, ValueError):
    """Une opération crée un conflit de programmation."""


class StorageError(FestivalError):
    """Impossible de lire ou sauvegarder les données."""
