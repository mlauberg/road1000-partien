#!/usr/bin/env python3
"""
Stand speichern und laden ohne Zip: progress.json und drills.json leben in der Datenbank des Artefakts "Road to 1000"
(ArtifactData Werkzeug von Claude). Dieses Skript uebersetzt zwischen den Dateien und den Dokumenten.

    python3 sync.py import <ordner>   nach ArtifactData list (partien, drills, drill_log, je out_dir=<ordner>) und get meta/stand:
                                      baut progress.json und drills.json und merkt sich in .sync_state.json, was schon in der Datenbank ist
    python3 sync.py export <ordner>   schreibt NEUE Dokumente nach <ordner>/... und druckt die Eintraege fuer ArtifactData batch

Alles ist Anlegen, nie Aendern (deshalb braucht es keine Versionsnummern):
    partien/<spiel id>      ein Dokument je Partie (Eintrag aus progress.json)
    drills/<D id>           ein Dokument je Aufgabe, fester Teil (Stellung, Loesung, Grund, Anlegedatum)
    drill_log/<D id>-<n>    ein Dokument je Antwort (Datum, ok oder fail); Serie, Faelligkeit und erledigt werden daraus berechnet
    meta/stand              player, goal, stufe (das einzige Dokument, das sich aendert: vor dem Schreiben mit get lesen, Version mitgeben)
"""
import sys, os, json, glob, datetime
BASE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(BASE, ".sync_state.json")
PROGRESS, DRILLS = os.path.join(BASE, "progress.json"), os.path.join(BASE, "drills.json")
STATIC = ("id", "fen", "lastmove", "played", "best", "accepted", "line", "move_no", "stufe", "grund", "win_before", "win_after", "user_white", "game", "due0")


def load_dir(d, coll):
    out = {}
    for f in sorted(glob.glob(os.path.join(d, coll, "*.json"))):
        out[os.path.basename(f)[:-5]] = json.load(open(f, encoding="utf-8"))
    return out


def replay(item, history):
    """Serie, Faelligkeit, erledigt aus der Antwortfolge (gleiche Regeln wie drill.py reveal)."""
    streak, due, done = 0, item.get("due0") or item.get("due") or datetime.date.today().isoformat(), False
    for h in history:
        day = datetime.date.fromisoformat(h["d"])
        if h["r"] == "ok":
            streak += 1
            if streak >= 3:
                done = True
            due = (day + datetime.timedelta(days={1: 3, 2: 7}.get(streak, 7))).isoformat()
        else:
            streak = 0
            due = (day + datetime.timedelta(days=1)).isoformat()
    return {"tries": len(history), "streak": streak, "due": due, "done": done, "history": history}


def do_import(d):
    games = sorted(load_dir(d, "partien").values(), key=lambda g: (g.get("ende", g.get("date", "")), g["id"]))
    statics = load_dir(d, "drills")
    logs = load_dir(d, "drill_log")
    items = []
    for did, st in sorted(statics.items()):
        hist = [logs[k] for k in sorted(logs) if logs[k].get("drill") == did]
        hist = [{"d": h["d"], "r": h["r"]} for h in sorted(hist, key=lambda h: h.get("n", 0))]
        it = {k: st[k] for k in STATIC if k in st}
        it.update(replay(it, hist))
        items.append(it)
    meta = {"player": "neogon51", "goal": 1000}
    mf = os.path.join(d, "meta", "stand.json")
    if os.path.exists(mf):
        meta.update({k: v for k, v in json.load(open(mf, encoding="utf-8")).items() if k in ("player", "goal", "stufe")})
    json.dump({"player": meta["player"], "goal": meta["goal"], "games": games}, open(PROGRESS, "w"), indent=1, ensure_ascii=False)
    json.dump({"items": items}, open(DRILLS, "w"), indent=1, ensure_ascii=False)
    json.dump({"partien": sorted(g["id"] for g in games), "drills": sorted(statics), "drill_log": sorted(logs), "stufe": meta.get("stufe")},
              open(STATE, "w"), indent=1)
    print(f"import: {len(games)} Partien, {len(items)} Drills ({sum(1 for i in items if not i['done'])} offen), {len(logs)} Antworten -> progress.json, drills.json"
          + (f" | Stufe laut Datenbank: {meta['stufe']}" if meta.get("stufe") else ""))


def do_export(d):
    state = json.load(open(STATE)) if os.path.exists(STATE) else {"partien": [], "drills": [], "drill_log": []}
    prog = json.load(open(PROGRESS)) if os.path.exists(PROGRESS) else {"player": "neogon51", "goal": 1000, "games": []}
    drills = json.load(open(DRILLS)) if os.path.exists(DRILLS) else {"items": []}
    writes = []

    def put(coll, did, body):
        os.makedirs(os.path.join(d, coll), exist_ok=True)
        path = os.path.join(d, coll, did + ".json")
        json.dump(body, open(path, "w"), indent=1, ensure_ascii=False)
        writes.append({"op": "set", "collection": coll, "doc_id": did, "file_path": os.path.abspath(path)})

    for g in prog["games"]:
        if g["id"] not in state["partien"]:
            put("partien", g["id"], g)
    for it in drills["items"]:
        if it["id"] not in state["drills"]:
            st = {k: it[k] for k in STATIC if k in it}
            st["due0"] = it.get("due0") or it.get("due")
            put("drills", it["id"], st)
        for n, h in enumerate(it.get("history", [])):
            key = f"{it['id']}-{n:03d}"
            if key not in state["drill_log"]:
                put("drill_log", key, {"drill": it["id"], "n": n, "d": h["d"], "r": h["r"]})
    os.makedirs(d, exist_ok=True)
    json.dump(writes, open(os.path.join(d, "batch.json"), "w"), indent=1)
    try:
        sys.path.insert(0, BASE); from analyze import STUFE
    except Exception:
        STUFE = None
    print(f"export: {len(writes)} neue Dokumente. Eintraege fuer ArtifactData batch (max 50 je Aufruf, ohne if_version) in {os.path.join(d, 'batch.json')}")
    for w in writes:
        print("  " + json.dumps(w, ensure_ascii=False))
    if STUFE is not None and state.get("stufe") not in (None, STUFE):
        print(f"STUFE in analyze.py ist {STUFE}, Datenbank sagt {state.get('stufe')}: meta/stand mit get lesen und mit set (if_version) auf {{player, goal, stufe: {STUFE}}} setzen.")


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] not in ("import", "export"):
        print(__doc__); sys.exit(1)
    (do_import if sys.argv[1] == "import" else do_export)(sys.argv[2])
