"""Verify Hindi endpoints return Devanagari (not romanized). Shell-safe check."""
import json
import sys
import urllib.request

BASE = "http://127.0.0.1:8000"


def dev_ratio(s: str) -> tuple[int, int]:
    dev = sum(1 for c in s if 0x900 <= ord(c) <= 0x97F)
    lat = sum(1 for c in s if c.isascii() and c.isalpha())
    return dev, lat


def get(path: str):
    with urllib.request.urlopen(BASE + path, timeout=30) as r:
        return json.load(r)


def post(path: str, body: dict):
    req = urllib.request.Request(
        BASE + path, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


ok = True
print("ADVISORY (lang=hi):")
for z in ["DL-ITO", "DL-WAZIRPUR", "DL-DWARKA"]:
    d = get(f"/advisory?zone={z}&persona=elderly&horizon=24&lang=hi")
    dev, lat = dev_ratio(d["message"])
    verdict = "DEVANAGARI OK" if dev > lat else "ROMANIZED!"
    ok = ok and dev > lat
    print(f"  {d['zone_name']:16} dev={dev:3d} lat={lat:3d} -> {verdict}")

print("CHAT (lang=hi):")
d = post("/chat", {"zone": "DL-ANANDVIHAR",
                   "message": "kya mera bacha bahar khel sakta hai?", "lang": "hi"})
dev, lat = dev_ratio(d["reply"])
ok = ok and dev > lat
print(f"  reply dev={dev} lat={lat} -> {'DEVANAGARI OK' if dev > lat else 'ROMANIZED!'}")

print("\nRESULT:", "ALL DEVANAGARI - PASS" if ok else "SOME ROMANIZED - FAIL")
sys.exit(0 if ok else 1)
