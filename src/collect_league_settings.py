
from src.espn_connection import connect_to_league

def main():
    league = connect_to_league()

    print("\n===== AVAILABLE LEAGUE SETTINGS =====")
    settings = league.settings

    print("\nAvailable attributes:")
    for attribute in dir(settings):
        if not attribute.startswith("_"):
            value = getattr(settings, attribute)
            if not callable(value):
                print(f"{attribute}: {value}")

    print("\n===== LEAGUE INFORMATION =====")

    print(f"League ID: {league.league_id}")
    print(f"Season: {league.year}")
    print(f"Number of teams: {len(league.teams)}")

if __name__ == "__main__":
    main()
