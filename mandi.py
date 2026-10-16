"""Live mandi prices from the free data.gov.in (Agmarknet) dataset.
Put your free key in a file named data_gov_key.txt (next to app.py) OR set env var DATA_GOV_KEY.
Never upload the key to GitHub (add data_gov_key.txt to .gitignore)."""
import os, json, time, urllib.parse, urllib.request
from datetime import datetime

RESOURCE = "9ef84268-d588-465a-a308-a864a43d0070"
_cache = {}

def _key():
    k = os.environ.get("DATA_GOV_KEY", "").strip()
    if not k and os.path.exists("data_gov_key.txt"):
        k = open("data_gov_key.txt").read().strip()
    return k

def _summarize(records):
    rows = []
    for r in records:
        try:
            rows.append({"market": r["market"], "district": r.get("district", ""),
                         "modal": float(r["modal_price"]),
                         "date": datetime.strptime(r["arrival_date"], "%d/%m/%Y")})
        except Exception:
            continue
    if not rows:
        return None
    latest = max(r["date"] for r in rows)
    rows = [r for r in rows if (latest - r["date"]).days <= 2]      # last 3 days only
    rows.sort(key=lambda r: (r["district"].lower() != "kolhapur", -r["modal"]))   # Kolhapur first
    avg = sum(r["modal"] for r in rows) / len(rows)
    return {"avg_modal": round(avg), "date": latest.strftime("%d %b %Y"), "count": len(rows),
            "markets": [{"market": r["market"], "district": r["district"], "modal": round(r["modal"])}
                        for r in rows[:5]]}

def get_mandi_price(commodity, state="Maharashtra"):
    key = _key()
    if not key:
        return {"error": "nokey"}
    ck = (commodity, state)
    if ck in _cache and time.time() - _cache[ck][0] < 3600:
        return _cache[ck][1]
    try:
        q = urllib.parse.urlencode({"api-key": key, "format": "json", "limit": 300,
                                    "filters[state]": state, "filters[commodity]": commodity})
        with urllib.request.urlopen(f"https://api.data.gov.in/resource/{RESOURCE}?{q}", timeout=10) as r:
            records = json.load(r).get("records", [])
        res = _summarize(records) or {"error": "nodata"}
    except Exception:
        res = {"error": "nodata"}
    if "error" not in res:
        _cache[ck] = (time.time(), res)
    return res
