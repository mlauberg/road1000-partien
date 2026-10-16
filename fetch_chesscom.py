#!/usr/bin/env python3
"""
Holt neue Partien von chess.com und legt sie als PGN in inbox/ ab. Nur Python Standardbibliothek.
Laeuft in der GitHub Action .github/workflows/fetch.yml (Ausloeser: `python3 analyze.py --fetch` aus dem Chat),
nicht im Chat selbst (von dort ist api.chess.com nicht erreichbar).
Quelle: chess.com Published Data API, oeffentlich, kostenlos, ohne Login. Jeder Lauf fragt den laufenden und den
vorigen Monat frisch ab (kein Cache, zwei Anfragen).

    python3 fetch_chesscom.py                neue Partien seit dem letzten Lauf
    python3 fetch_chesscom.py --all          alle Partien aus laufendem und vorigem Monat (Nachholen)
    python3 fetch_chesscom.py --class alle   auch Blitz, Bullet, Daily (Standard: nur rapid)
    python3 fetch_chesscom.py --dry          nur anzeigen, nichts schreiben

Dateien:
    inbox/alle.pgn                    alle bisher geholten Partien in einer Datei (das liest analyze.py)
    inbox/<datum>_<gegner>_<id>.pgn   eine Datei je Partie
    inbox/.fetch_state.json           Stand (letzte Partie, bekannte IDs), wird mit committet

Umgebung (optional, kommt in der Action aus den Repo Secrets, damit nichts Persoenliches im Code steht):
    ROAD1000_USER      chess.com Name (Standard neogon51)
    ROAD1000_CONTACT   Mailadresse fuer den User-Agent (chess.com bittet darum, keine Pflicht)
"""
import sys
import os
import json
import re
import datetime
import urllib.request
import urllib.error

USER = os.environ.get("ROAD1000_USER", "neogon51")
CONTACT = os.environ.get("ROAD1000_CONTACT", "")
BASE = os.path.dirname(os.path.abspath(__file__))
INBOX = os.path.join(BASE, "inbox")
STATE = os.path.join(INBOX, ".fetch_state.json")
API = "https://api.chess.com/pub/player/{user}/games/{y}/{m:02d}"
UA = f"road-to-1000/1.2 (username: {USER}" + (f"; contact: {CONTACT})" if CONTACT else ")")


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json", "Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def months(n=2):
    """Laufender und voriger Monat nach UTC, aelterer zuerst."""
    today = datetime.datetime.now(datetime.timezone.utc).date()
    out, y, m = [], today.year, today.month
    for _ in range(n):
        out.append((y, m))
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    return list(reversed(out))


def game_id(g):
    return g.get("uuid") or g.get("url", "").rstrip("/").split("/")[-1]


def clean(s):
    return re.sub(r"[^A-Za-z0-9_.-]", "_", s)[:24]


def utc_date(ts):
    return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime("%Y-%m-%d")


def describe(g):
    me = g["white"] if g["white"]["username"].lower() == USER.lower() else g["black"]
    opp = g["black"] if me is g["white"] else g["white"]
    farbe = "Weiss" if me is g["white"] else "Schwarz"
    uhr = "ja" if "%clk" in g.get("pgn", "") else "nein"
    return (f"{utc_date(g.get('end_time', 0))} {g.get('time_class')} {g.get('time_control')} | "
            f"{USER} ({me.get('rating')}) als {farbe} gegen {opp['username']} ({opp.get('rating')}) | "
            f"{me.get('result')} | Uhr im PGN: {uhr}"), opp["username"]


def main(argv):
    want_all, dry = "--all" in argv, "--dry" in argv
    cls = argv[argv.index("--class") + 1] if "--class" in argv else "rapid"
    os.makedirs(INBOX, exist_ok=True)
    state = {"last_end_time": 0, "seen": []}
    if os.path.exists(STATE):
        with open(STATE, encoding="utf-8") as fh:
            state.update(json.load(fh))
    seen, new, gesehen = set(state["seen"]), [], []
    for y, m in months(2):
        try:
            data = get_json(API.format(user=USER, y=y, m=m))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                gesehen.append(f"{y}-{m:02d} leer"); continue  # Monat ohne Partien
            sys.exit(f"HTTP {e.code} bei {y}-{m:02d}: {e.reason}")
        except (urllib.error.URLError, TimeoutError) as e:
            sys.exit(f"Keine Verbindung zu api.chess.com: {e}")
        gesehen.append(f"{y}-{m:02d} {len(data.get('games', []))} Partien bei chess.com")
        for g in data.get("games", []):
            if cls != "alle" and g.get("time_class") != cls:
                continue
            if g.get("rules", "chess") != "chess" or "pgn" not in g:
                continue
            gid = game_id(g)
            if gid in seen or (not want_all and g.get("end_time", 0) <= state["last_end_time"]):
                continue
            seen.add(gid)
            new.append(g)
    new.sort(key=lambda g: g.get("end_time", 0))
    if not new:
        print(f"Keine neuen Partien ({', '.join(gesehen)}).")
        return
    for g in new:
        line, opp = describe(g)
        print(line)
        if dry:
            continue
        name = f"{utc_date(g.get('end_time', 0))}_{clean(opp)}_{clean(game_id(g))[-10:]}.pgn"
        with open(os.path.join(INBOX, name), "w", encoding="utf-8") as fh:
            fh.write(g["pgn"].strip() + "\n")
        state["last_end_time"] = max(state["last_end_time"], g.get("end_time", 0))
    if dry:
        return
    state["seen"] = sorted(seen)[-500:]
    with open(STATE, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=1)
    singles = sorted(f for f in os.listdir(INBOX) if f.endswith(".pgn") and f != "alle.pgn")
    parts = []
    for x in singles:
        with open(os.path.join(INBOX, x), encoding="utf-8") as sfh:
            parts.append(sfh.read().strip())
    with open(os.path.join(INBOX, "alle.pgn"), "w", encoding="utf-8") as fh:
        fh.write("\n\n".join(parts) + "\n")
    print(f"{len(new)} neue Partien ({', '.join(gesehen)}), alle.pgn: {len(singles)} Partien")


if __name__ == "__main__":
    main(sys.argv[1:])
