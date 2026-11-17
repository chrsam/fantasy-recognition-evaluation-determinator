
import inspect
from espn_api.football import League

def inspect_method(method_name):
    method = getattr(League, method_name, None)
    if method is None:
        print(f"{method_name}: Not available")
        return

    print(f"\n===== {method_name} =====")
    print(f"Signature {inspect.signature(method)}")

    print("\nDocumentation:")
    print(inspect.getdoc(method) or "No documentation available.")

def main():
    for method_name in [
        "free_agents",
        "player_info",
        "box_scores",
    ]:
        inspect_method(method_name)

if __name__ == "__main__":
    main()
