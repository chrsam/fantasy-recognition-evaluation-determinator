
import inspect
from src.espn_connection import connect_to_league

def explore_free_agents():
    
    league = connect_to_league()
    
    print("===== ESPN FREE AGENT API INSPECTION =====")
    for name in dir(league):
        if any(
            keyword in name.lower()
            for keyword in ["free", "player", "waiver"]
        ):
            attribute = getattr(league, name)

            print(f"\nMethod/attribute: {name}")
            print(f"Callable: {callable(attribute)}")

            if callable(attribute):
                try:
                    print(f"Signature: {inspect.signature(attribute)}")
                except (TypeError, ValueError):
                    print("Signature unavailable")

if __name__ == "__main__":
    explore_free_agents()
