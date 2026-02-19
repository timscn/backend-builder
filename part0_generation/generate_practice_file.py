import json
import random
from pathlib import Path


def generate_practice_file(output_path: str = None) -> str:
    # Get repo root (one level up from script location)
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    
    if output_path is None:
        output_path = str(repo_root / "output" / "logs.jsonl")
    
    features = ["map", "chat", "settings", "profile"]
    actions = ["start", "end"]

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        for i in range(1, 101):
            # 80% chance of a valid log
            if i % 10 == 0:
                # ERROR TYPE 1: Malformed JSON (broken string)
                f.write(f'{{"user_id": {i}, "action": "start" -- BROKEN\n')
            elif i % 15 == 0:
                # ERROR TYPE 2: Missing "feature" key
                log = {"user_id": i, "timestamp": "2024-03-01T12:00:00Z", "action": "end"}
                f.write(json.dumps(log) + "\n")
            elif i % 25 == 0:
                # ERROR TYPE 3: Bad timestamp format
                log = {"user_id": i, "feature": "map", "timestamp": "NOT-A-DATE", "action": "start"}
                f.write(json.dumps(log) + "\n")
            else:
                # VALID LOG
                log = {
                    "user_id": random.randint(1, 5),
                    "feature": random.choice(features),
                    "timestamp": f"2024-03-01T10:{i:02d}:00Z",
                    "action": random.choice(actions),
                }
                f.write(json.dumps(log) + "\n")
    
    return output_path


if __name__ == "__main__":
    output_path = generate_practice_file()
    print(f"{output_path} created with 100 lines!")

