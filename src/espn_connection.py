
import os

from dotenv import load_dotenv
from espn_api.football import League

def connect_to_league():
    # Load credentials from the local .env file
    load_dotenv()

    # Retrieve configuration
    league_id = os.getenv("ESPN_LEAGUE_ID")
    season = os.getenv("ESPN_SEASON")
    espn_s2 = os.getenv("ESPN_S2")
    swid = os.getenv("ESPN_SWID")

    # Check that required configuration exists
    if not all([league_id, season, espn_s2, swid]):
        raise ValueError(
            "Missing ESPN configuration. "
            "Check your local .env file."
        )

    # Connect to ESPN
    league = League(
        league_id=int(league_id),
        year=int(season),
        espn_s2=espn_s2,
        swid=swid
    )

    return league

def main():
    print("Connecting to ESPN...")

    league = connect_to_league()

    print("\nConection successful!")
    print("=======================")

    print(f"League ID: {league.league_id}")
    print(f"Season: {league.year}")
    print(f"Number of teams: {len(league.teams)}")

    print("\n League Teams:")

    for team in league.teams:
        print(f"- {team.team_name}")

if __name__ == "__main__":
    main()