
from src.espn_connection import connect_to_league

def test_historical_stats():
    league = connect_to_league()

    # Test several completed weeks.
    weeks_to_test = [6, 7, 8, 9, 10]

    for week in weeks_to_test:
        print(f"\n===== REQUESTED WEEK: {week} =====")

        try: 
            players = league.free_agents(
                week=week,
                size=5,
                position="RB"
            )

            print(f"Players returned: {len(players)}")
            if not players:
                continue

            player = players[0]

            print(f"Player: {player.name}")
            print(f"Available stats keys: {list(player.stats.keys())}")

            weekly_stats = player.stats.get(week, {})

            print(
                f"Actual points for Week {week}: "
                f"{weekly_stats.get('points', 'NOT AVAILABLE')}"
            )

        except Exception as error:
            print(f"Error: {error}")

if __name__ == "__main__":
    test_historical_stats()
