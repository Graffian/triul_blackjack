import json
import time
import urllib.request
import urllib.error

WDA_URL = "http://localhost:8100"
_session_id = None


def _request(method, endpoint, data=None, retries=3):
    url = f"{WDA_URL}{endpoint}"
    body = json.dumps(data).encode() if data else None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=body, method=method)
            req.add_header("Content-Type", "application/json")
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            err_body = e.read().decode()
            if attempt == retries - 1:
                raise RuntimeError(f"HTTP {e.code} on {method} {endpoint}: {err_body}")
            time.sleep(1)
        except urllib.error.URLError as e:
            if attempt == retries - 1:
                raise RuntimeError(f"Connection error on {endpoint}: {e.reason}")
            time.sleep(1)


def start_session():
    global _session_id
    status = _request("GET", "/status")
    v = status.get("value", {})
    sid = status.get("sessionId") or v.get("sessionId")
    if sid:
        _session_id = sid
        return sid
    result = _request("POST", "/session", {"capabilities": {"alwaysMatch": {}}})
    sid = result.get("sessionId") or result.get("value", {}).get("sessionId")
    if not sid:
        raise RuntimeError(f"Failed to create session: {result}")
    _session_id = sid
    print(f"Created session: {sid}")
    return sid


def _with_session(path):
    return f"/session/{_session_id}{path}" if _session_id else path


def screenshot():
    result = _request("GET", _with_session("/screenshot"))
    value = result.get("value")
    if not value:
        raise RuntimeError(f"Unexpected screenshot response: {result}")
    return value


def tap(x, y):
    payload = {"sequence": [{"x": x, "y": y, "duration": 0.05}]}
    _request("POST", _with_session("/wda/tapScreenPointSequence"), payload)


def drag(from_x, from_y, to_x, to_y, duration=0.3):
    payload = {"fromX": from_x, "fromY": from_y, "toX": to_x, "toY": to_y, "duration": duration}
    _request("POST", _with_session("/wda/dragfromto"), payload)


def screen_size():
    status = _request("GET", "/status")
    v = status.get("value", {})
    sw = v.get("screenWidth", 1170)
    sh = v.get("screenHeight", 2532)
    return sw, sh
