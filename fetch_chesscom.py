#!/usr/bin/env python3
"""
Holt neue Partien von chess.com und legt sie als PGN ab. Nur Python Standardbibliothek (3.8 oder neuer).
Quelle: chess.com Published Data API (oeffentliche Daten, kostenlos, kein Login). Serieller Abruf ist laut
chess.com unbegrenzt, die Endpunkte aktualisieren sich laut Doku hoechstens alle 12 Stunden. Darum fragt das
Script bedingt ab (ETag, If-None-Match): unveraendert heisst Antwort 304 ohne Daten, das kostet niemanden etwas.

    python3 fetch_chesscom.py                neue Partien seit dem letzten Lauf -> inbox/<datum>_<gegner>_<id>.pgn
    python3 fetch_chesscom.py --all          alle Partien aus laufendem und vorigem Monat (erster Lauf oder Nachholen)
    python3 fetch_chesscom.py --class alle   auch Blitz, Bullet, Daily (Standard: nur rapid)
    python3 fetch_chesscom.py --dry          nur anzeigen, nichts schreiben, nichts schicken
    python3 fetch_chesscom.py --git          danach inbox/ committen und pushen, ausstehende Commits ebenfalls

Dateien:
    inbox/alle.pgn               alle bisher geholten Partien in einer Datei (das liest der Schach Chat)
    inbox/<datum>_<gegner>_<id>.pgn   eine Datei je Partie
    inbox/.fetch_state.json      Stand (letzte Partie, bekannte IDs, ETags je Monat), wird mit committet
    out/neu_<zeit>.pgn           Sammeldatei je Lauf mit neuen Partien, nur fuer den ntfy Anhang, nicht im Git

Einstellungen kommen aus der Umgebung (systemd EnvironmentFile), damit das Script selbst ohne persoenliche
Daten im oeffentlichen Repo liegen kann:
    ROAD1000_USER      chess.com Name (Standard neogon51)
    ROAD1000_CONTACT   Mailadresse fuer den User-Agent (chess.com bittet darum, keine Pflicht)
    NTFY_URL           optional, z. B. https://ntfy.deinserver/road1000, dann Push je Lauf mit neuen Partien
    NTFY_TOKEN         optional, Bearer Token fuer ntfy
"""
import sys
import os
import json
import re
import datetime
import subprocess
import urllib.request
import urllib.error

USER = os.environ.get("ROAD1000_USER", "neogon51")
CONTACT = os.environ.get("ROAD1000_CONTACT", "")
BASE = os.path.dirname(os.path.abspath(__file__))
INBOX = os.path.join(BASE, "inbox")
OUT = os.path.join(BASE, "out")
STATE = os.path.join(INBOX, ".fetch_state.json")
API = "https://api.chess.com/pub/player/{user}/games/{y}/{m:02d}"
UA = f"road-to-1000/1.1 (username: {USER}" + (f"; contact: {CONTACT})" if CONTACT else ")")
KEEP_BUNDLES = 20


def get_json(url, etag=None):
    """Liefert (daten, etag). daten ist None bei 304 (unveraendert)."""
    headers = {"User-Agent": UA, "Accept": "application/json"}
    if etag:
        headers["If-None-Match"] = etag
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r), r.headers.get("ETag")
    except urllib.error.HTTPError as e:
        if e.code == 304:
            return None, etag
        raise


def months(n=2):
    """Laufender und voriger Monat nach UTC, aelterer zuerst."""
    today = datetime.datetime.now(datetime.timezone.utc).date()
    out = []
    y, m = today.year, today.month
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


def ntfy(path, title, message):
    url = os.environ.get("NTFY_URL")
    if not url:
        return False
    with open(path, "rb") as fh:
        data = fh.read()
    headers = {"Title": title.encode("ascii", "ignore").decode(),
               "Message": message.encode("ascii", "ignore").decode(),
               "Filename": os.path.basename(path), "Content-Type": "application/x-chess-pgn"}
    tok = os.environ.get("NTFY_TOKEN")
    if tok:
        headers["Authorization"] = "Bearer " + tok
    req = urllib.request.Request(url, data=data, headers=headers, method="PUT")
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status < 300


def git(*args):
    r = subprocess.run(["git", *args], cwd=BASE, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def git_sync(message):
    """Committet inbox/ falls geaendert, holt Upstream per rebase, pusht alles Ausstehende. Liefert True bei Erfolg."""
    git("add", "-A", "inbox")
    rc, _ = git("diff", "--cached", "--quiet")
    if rc != 0:
        rc, out = git("commit", "-qm", message)
        if rc != 0:
            print(f"git commit: {out[:200]}", file=sys.stderr)
            return False
    rc, out = git("pull", "-q", "--rebase")
    if rc != 0:
        print(f"git pull: {out[:200]}", file=sys.stderr)
        return False
    rc, out = git("rev-list", "--count", "@{u}..HEAD")
    if rc == 0 and out.strip() == "0":
        return True
    rc, out = git("push", "-q")
    if rc != 0:
        print(f"git push: {out[:200]}", file=sys.stderr)
        return False
    print("git push ok.")
    return True


def main(argv):
    want_all = "--all" in argv
    dry = "--dry" in argv
    use_git = "--git" in argv
    cls = "rapid"
    if "--class" in argv:
        cls = argv[argv.index("--class") + 1]
    os.makedirs(INBOX, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)
    if os.path.exists(STATE):
        with open(STATE, encoding="utf-8") as fh:
            state = json.load(fh)
    else:
        state = {"last_end_time": 0, "seen": [], "etags": {}}
    state.setdefault("etags", {})
    seen = set(state.get("seen", []))
    new = []
    for y, m in months(2):
        key = f"{y}-{m:02d}"
        url = API.format(user=USER, y=y, m=m)
        try:
            data, etag = get_json(url, None if want_all else state["etags"].get(key))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                continue
            print(f"HTTP {e.code} bei {key}: {e.reason}", file=sys.stderr)
            sys.exit(1)
        except (urllib.error.URLError, TimeoutError) as e:
            print(f"Keine Verbindung zu api.chess.com: {e}", file=sys.stderr)
            sys.exit(1)
        if data is None:
            continue  # 304, Monat unveraendert
        if etag and not dry:
            state["etags"][key] = etag
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
        print("Keine neuen Partien.")
        if not dry:
            with open(STATE, "w", encoding="utf-8") as fh:
                json.dump(state, fh, indent=1)
            if use_git and not git_sync("Stand aktualisiert"):
                sys.exit(1)
        return
    written = []
    for g in new:
        line, opp = describe(g)
        print(line)
        name = f"{utc_date(g.get('end_time', 0))}_{clean(opp)}_{clean(game_id(g))[-10:]}.pgn"
        path = os.path.join(INBOX, name)
        if not dry:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(g["pgn"].strip() + "\n")
            written.append((path, g, line))
        state["last_end_time"] = max(state["last_end_time"], g.get("end_time", 0))
    if dry:
        return
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    bundle = os.path.join(OUT, f"neu_{stamp}.pgn")
    with open(bundle, "w", encoding="utf-8") as fh:
        fh.write("\n\n".join(g["pgn"].strip() for _, g, _ in written) + "\n")
    old = sorted(f for f in os.listdir(OUT) if f.startswith("neu_") and f.endswith(".pgn"))
    for f in old[:-KEEP_BUNDLES]:
        os.remove(os.path.join(OUT, f))
    state["seen"] = sorted(seen)[-500:]
    with open(STATE, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=1)
    singles = sorted(f for f in os.listdir(INBOX) if f.endswith(".pgn") and f != "alle.pgn")
    with open(os.path.join(INBOX, "alle.pgn"), "w", encoding="utf-8") as fh:
        parts = []
        for x in singles:
            with open(os.path.join(INBOX, x), encoding="utf-8") as sfh:
                parts.append(sfh.read().strip())
        fh.write("\n\n".join(parts) + "\n")
    print(f"{len(written)} Partien -> {bundle} | alle.pgn: {len(singles)} Partien")
    ok = True
    if use_git:
        ok = git_sync(f"{len(written)} neue Partien {stamp}")
    try:
        if ntfy(bundle, f"Road to 1000: {len(written)} neue Partie(n)", "\n".join(l for _, _, l in written)[:900]):
            print("ntfy Push gesendet.")
    except Exception as e:  # ntfy ist Komfort, kein Fehlerfall fuer den Timer
        print(f"ntfy Push fehlgeschlagen: {e}", file=sys.stderr)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
