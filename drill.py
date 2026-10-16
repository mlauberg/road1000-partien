#!/usr/bin/env python3
"""
Drill Pool: deine eigenen Fehlerstellungen als Quiz, nur zur aktuellen Stufe.
    python3 drill.py add games/<report>.json      nimmt Drillkandidaten des Spiels auf (Stufe <= STUFE, Verlust >= 15 %), Pool max 10 offen
    python3 drill.py quiz [n]                     rendert bis zu n faellige Aufgaben OHNE Pfeile und ohne Tipp
    python3 drill.py reveal <id> [--ok|--fail]    Aufloesung mit Pfeilen, Ergebnis wird gespeichert
    python3 drill.py stats                        Pool, faellig, Trefferquote
    python3 drill.py prune                        wirft alles raus, was nicht zur Stufe passt (nach Stufenwechsel oder Regelaenderung)

    python3 drill.py speed                        Schnellrunde: alle erledigten Aufgaben als Quiz, 10 Sekunden je Stellung (woechentlich)

Wiederholung (verteiltes Ueben): richtig -> in 3 Tagen nochmal, dann in 7 Tagen, dreimal hintereinander richtig -> erledigt. Falsch -> morgen wieder, Serie auf null.
Richtig ist jeder Zug aus "accepted" (innerhalb 5 Punkten Gewinnchance zum besten Zug).
STUFE steht in analyze.py und wird dort umgestellt, wenn --progress die naechste Stufe freigibt.
"""
import sys, os, json, datetime
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import chess  # noqa: E402
import show  # noqa: E402
from analyze import STUFE  # noqa: E402   (1 Captures, 2 Checks, 3 Attacks; wird in analyze.py umgestellt)

POOL_MAX = 10        # offene Aufgaben
MIN_DROP = 15
DRILL_FILE = os.path.join(BASE, "drills.json")
DRILL_DIR = os.path.join(BASE, "drills")
TODAY = datetime.date.today


def load():
    return json.load(open(DRILL_FILE)) if os.path.exists(DRILL_FILE) else {"items": []}


def save(d):
    json.dump(d, open(DRILL_FILE, "w"), indent=1, ensure_ascii=False)


def open_items(d):
    return [x for x in d["items"] if not x["done"]]


def add(report_path):
    r = json.load(open(report_path)); d = load()
    known = {x["fen"] for x in d["items"]}
    cands = [m for m in r["critical"] if 0 < m.get("drill_stufe", 0) <= STUFE and m["drop"] >= MIN_DROP and m["fen_before"] not in known and m.get("best")]
    cands.sort(key=lambda m: -m["drop"])
    free = POOL_MAX - len(open_items(d))
    n = 0
    for m in cands[:max(0, free)]:
        lm = show.lastmove_before(r, m["ply"])
        d["items"].append({
            "id": f"D{len(d['items']) + 1:03d}", "fen": m["fen_before"], "lastmove": lm.uci() if lm else None,
            "played": m["san"], "best": m["best"], "accepted": m.get("accepted", [m["best"]]), "line": m.get("best_line", ""),
            "move_no": m["move_no"], "stufe": m["drill_stufe"], "grund": m.get("drill_grund", ""),
            "win_before": m["win_before"], "win_after": m["win_after"], "user_white": r["user_color"] == "Weiss",
            "game": os.path.basename(report_path)[:-5], "streak": 0, "tries": 0, "done": False, "due": TODAY().isoformat(), "history": [],
        })
        n += 1
    save(d)
    print(f"{n} neue Aufgaben ({len(cands) - n} Kandidaten nicht aufgenommen, Pool voll oder Duplikat). Offen: {len(open_items(d))} / max {POOL_MAX}")


def quiz(n=3):
    d = load(); os.makedirs(DRILL_DIR, exist_ok=True)
    today = TODAY().isoformat()
    items = [x for x in open_items(d) if x["due"] <= today]
    items.sort(key=lambda x: (x["due"], -x["tries"], x["id"]))
    if not items:
        print("Heute nichts faellig."); return []
    outs = []
    for it in items[:n]:
        who = "Weiß" if it["user_white"] else "Schwarz"
        cap = [f"{it['id']}: du bist {who}, du bist am Zug.", f"(Spiel {it['game'][:10]}, Zug {it['move_no'].rstrip('.')})"]
        out = os.path.join(DRILL_DIR, f"{it['id']}_quiz.png")
        show.render(it["fen"], out, chess.WHITE if it["user_white"] else chess.BLACK, lastmove=it["lastmove"], caption_lines=cap)
        outs.append(out); print(out)
    return outs


def reveal(did, result=None):
    d = load()
    it = next((x for x in d["items"] if x["id"] == did), None)
    if not it:
        print("unbekannte id"); return
    b = chess.Board(it["fen"])
    acc = [show.move_words(b, a) for a in it["accepted"] if a != it["best"]]
    cap = [f"{it['id']}: richtig ist {show.move_words(b, it['best'])} (grün)" + (f", auch richtig: {', '.join(acc)}" if acc else ""),
           f"Gespielt hattest du {show.move_words(b, it['played'])} (rot): Gewinnchance {it['win_before']:.0f} % auf {it['win_after']:.0f} %. {show.umlaut(it['grund'])}",
           f"Weiter: {show.line_words(b, it['line'], 3)}"]
    os.makedirs(DRILL_DIR, exist_ok=True)
    out = os.path.join(DRILL_DIR, f"{it['id']}_loesung.png")
    show.render(it["fen"], out, chess.WHITE if it["user_white"] else chess.BLACK, played=it["played"], best=it["best"], lastmove=it["lastmove"], caption_lines=cap)
    if result in ("ok", "fail"):
        it["tries"] += 1
        it["history"].append({"d": TODAY().isoformat(), "r": result})
        if result == "ok":
            it["streak"] += 1
            if it["streak"] >= 3:
                it["done"] = True
            it["due"] = (TODAY() + datetime.timedelta(days={1: 3, 2: 7}.get(it["streak"], 7))).isoformat()
        else:
            it["streak"] = 0
            it["due"] = (TODAY() + datetime.timedelta(days=1)).isoformat()
        save(d)
    print(out)
    print(f"Richtig: {', '.join(it['accepted'])} | Variante: {it['line']} | {it['grund']}" + (" | ERLEDIGT" if it["done"] else f" | wieder am {it['due']}"))


def speed():
    """Woechentliche Schnellrunde: alle erledigten Aufgaben, 10 Sekunden je Stellung, ohne Spicken."""
    d = load(); os.makedirs(DRILL_DIR, exist_ok=True)
    items = [x for x in d["items"] if x["done"]]
    if not items:
        print("Noch nichts erledigt, Schnellrunde erst spaeter."); return []
    outs = []
    for it in items:
        who = "Weiß" if it["user_white"] else "Schwarz"
        cap = [f"Schnellrunde {it['id']}: du bist {who}, 10 Sekunden.", ""]
        out = os.path.join(DRILL_DIR, f"{it['id']}_speed.png")
        show.render(it["fen"], out, chess.WHITE if it["user_white"] else chess.BLACK, lastmove=it["lastmove"], caption_lines=cap)
        outs.append(out); print(out)
    print(f"{len(outs)} Stellungen. Loesungen: drill.py reveal <id> (ohne --ok/--fail, Schnellrunde zaehlt nicht fuer die Wiederholung).")
    return outs


def stats():
    d = load(); items = d["items"]
    if not items:
        print("Noch keine Aufgaben."); return
    today = TODAY().isoformat()
    op = open_items(d)
    tries = sum(x["tries"] for x in items)
    ok = sum(1 for x in items for h in x["history"] if h["r"] == "ok")
    print(f"Stufe {STUFE} | offen {len(op)} / max {POOL_MAX} | heute faellig {sum(1 for x in op if x['due'] <= today)} | erledigt {sum(1 for x in items if x['done'])} | "
          f"Versuche {tries}, richtig {ok} ({(100 * ok / tries) if tries else 0:.0f} %)")
    for x in sorted(op, key=lambda x: x["due"]):
        print(f"  {x['id']} faellig {x['due']} Stufe {x['stufe']} {x['grund']} ({x['move_no']} {x['played']} -> {x['best']}, {x['win_before'] - x['win_after']:.0f} %)")


def prune():
    d = load()
    before = len(d["items"])
    d["items"] = [x for x in d["items"] if x["done"] or (0 < x.get("stufe", 0) <= STUFE and x["win_before"] - x["win_after"] >= MIN_DROP)]
    save(d)
    print(f"{before - len(d['items'])} Aufgaben entfernt, {len(open_items(d))} offen")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        print(__doc__)
    elif a[0] == "add":
        add(a[1])
    elif a[0] == "quiz":
        quiz(int(a[1]) if len(a) > 1 else 3)
    elif a[0] == "reveal":
        reveal(a[1], "ok" if "--ok" in a else ("fail" if "--fail" in a else None))
    elif a[0] == "stats":
        stats()
    elif a[0] == "prune":
        prune()
    elif a[0] == "speed":
        speed()
    else:
        print(__doc__)
