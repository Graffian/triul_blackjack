import json
import os
import time
from mitmproxy import http

SEED_FILE = os.path.join(os.path.dirname(__file__), "last_seed.txt")

def response(flow: http.HTTPFlow):
    text = flow.response.text
    if "reportGameSessionIntermediateData" not in text:
        return
    try:
        data = json.loads(text)
        payload = data.get("data", {}).get("reportGameSessionIntermediateData")
        if not payload:
            return
        seed = payload.get("seed")
        game_id = payload.get("gameId")
        if seed is None:
            return
        record = {
            "seed": seed,
            "game_id": game_id,
            "tournament_type": payload.get("tournamentType"),
            "user_id": payload.get("userId"),
            "timestamp": time.time(),
        }
        with open(SEED_FILE, "w") as f:
            f.write(json.dumps(record))
        print(f"SEED_CAPTURED: seed={seed} game={game_id}")
    except (json.JSONDecodeError, KeyError, TypeError):
        pass
