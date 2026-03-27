"""
Daily score recorder for PORT-1000.
Runs via GitHub Actions. Fetches current scores for all ports and appends
to scores_history.json.

Uses scoring functions from data_logic.py (single source of truth).
"""
import json
import os
from datetime import datetime, timezone

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "scores_history.json")
TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")

# Import scoring logic from data_logic.py (the single source of truth).
from data_logic import load_all_ports


def main():
    print(f"[PORT-1000] Recording scores for {TODAY}")

    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)
    else:
        history = {}

    if TODAY not in history:
        history[TODAY] = {}

    ports = load_all_ports()
    recorded = 0

    for name, data in ports.items():
        try:
            score = data["total"]
            history[TODAY][name] = score
            print(f"  {name}: {score}")
            recorded += 1
        except Exception as e:
            print(f"  Error ({name}): {e}")

    if recorded > 0:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2)
        print(f"[PORT-1000] Done. {recorded} port scores recorded for {TODAY}")
    else:
        print(f"[PORT-1000] Warning: No scores could be recorded for {TODAY}")


if __name__ == "__main__":
    main()
