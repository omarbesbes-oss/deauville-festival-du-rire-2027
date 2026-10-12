import argparse
from datetime import date, datetime

from festival.storage import load_festival


def main():
    parser = argparse.ArgumentParser(description="Deauville Festival du Rire 2027")

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    # Commande : programme
    programme_parser = subparsers.add_parser(
        "programme",
        help="Afficher le programme d'une journée",
    )
    programme_parser.add_argument("day")

    # Commande : artists
    subparsers.add_parser(
        "artists",
        help="Afficher les artistes et leurs spectacles",
    )

    # Commande : now
    now_parser = subparsers.add_parser(
        "now",
        help="Afficher les spectacles en cours et les suivants",
    )
    now_parser.add_argument("moment")

    args = parser.parse_args()

    try:
        festival = load_festival("data/festival.json")

        if args.command == "programme":
            day = date.fromisoformat(args.day)

            print(f"\n=== PROGRAMME DU {day} ===")

            for show in festival.programme_for_day(day):
                print(f"{show.start:%d/%m %H:%M} | {show.title} | {show.venue.name}")

        elif args.command == "artists":
            print("\n=== ARTISTES ===")

            for artist, count in festival.artist_show_counts():
                print(f"{artist.name} : {count} spectacle(s)")

        elif args.command == "now":
            moment = datetime.fromisoformat(args.moment)

            print(f"\n=== EN COURS À {moment} ===")

            current = festival.currently_on_stage(moment)

            if not current:
                print("Aucun spectacle en cours.")

            for show in current:
                print(
                    f"{show.title} | {show.venue.name} | "
                    f"{show.start:%H:%M}-{show.end:%H:%M}"
                )

            print("\n=== 3 PROCHAINS SPECTACLES ===")

            for show in festival.next_performances(moment):
                print(f"{show.start:%d/%m %H:%M} | {show.title} | {show.venue.name}")

    except (ValueError, OSError, KeyError) as error:
        parser.exit(1, f"Erreur : {error}\n")


if __name__ == "__main__":
    main()
