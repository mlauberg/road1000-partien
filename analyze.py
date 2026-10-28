#!/usr/bin/env python3
"""
Road to 1000 - Stockfish Spielanalyse fuer neogon51 (v3, 16.10.2026).

    python3 analyze.py game.pgn      -> Report (Text + JSON + Bilder), traegt das Spiel in progress.json ein
    python3 analyze.py inbox/neu.pgn -> Datei mit mehreren Partien: jede neue wird analysiert, bekannte uebersprungen (--force: alle)
    python3 analyze.py --fetch       -> Normalweg bei "Analyse": stoesst den Abruf bei chess.com JETZT an (Push auf request.txt,
                                        die GitHub Action holt die Partien nach inbox/), wartet bis zu 3 Minuten auf die Marke
                                        inbox/.last_run.txt und analysiert dann alle neuen Partien. Braucht einen Klon mit Schreibrecht.
    python3 analyze.py --pull        -> Rueckfall ohne Schreibrecht: holt inbox/alle.pgn von INBOX_URL (GitHub raw), analysiert alle neuen
    python3 analyze.py --progress    -> Trend ueber alle Spiele, Stufe 1 Kennzahlen, Stufenfreigabe

Alle Bewertungen kommen von Stockfish. Zugklassen nur nach Verlust an Gewinnchance (wie Lichess):
BLUNDER >= 20 Punkte, FEHLER >= 10, UNGENAU >= 5. Geprueft am 16.10.2026: Tiefe 16 liefert dieselben
Blunder wie Tiefe 26 (27 von 27), die Loesung bei Tiefe 20 dieselbe wie bei Tiefe 26.
Statische Brettpruefungen (haengt, gratis) sind Heuristiken und werden nur gezaehlt, wenn die Engine
sie bestaetigt (Widerlegung = genau dieses Schlagen).
Mit N_WORKERS Engines parallel; gleiche Workerzahl = gleiche Zahlen.
"""
import sys, os, io, json, math, re, hashlib, datetime
from concurrent.futures import ThreadPoolExecutor

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import chess, chess.pgn, chess.engine  # noqa: E402

ENGINE_PATH = os.path.join(BASE, "engine", "stockfish")
GAMES_DIR = os.path.join(BASE, "games")
PROGRESS_FILE = os.path.join(BASE, "progress.json")
PLAYER = "neogon51"
INBOX_URL = "https://raw.githubusercontent.com/mlauberg/road1000-partien/main/inbox/alle.pgn"

DEPTH_FAST = 16       # jede Stellung
DEPTH_DEEP = 20       # Lektions- und Drillstellungen, 3 Varianten
DEPTH_PUNISH = 18     # Widerlegung nach dem Fehler
N_WORKERS = max(1, min(4, os.cpu_count() or 1))
HASH_MB = 256
STUFE = 1             # aktuelle Trainingsstufe: 1 Captures, 2 Checks, 3 Attacks. Hier umstellen, drill.py liest es mit.
DRILL_MIN_DROP = 15   # ab diesem Verlust (Prozentpunkte) wird eine Stellung Drillkandidat
ALT_WINDOW = 5        # Zuege innerhalb von 5 Punkten Gewinnchance zum besten gelten im Drill als richtig

PIECE_VAL = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}
PIECE_DE = {chess.PAWN: "Bauer", chess.KNIGHT: "Springer", chess.BISHOP: "Laeufer",
            chess.ROOK: "Turm", chess.QUEEN: "Dame", chess.KING: "Koenig"}

OPENINGS = {
    "e4": "Koenigsbauer (1.e4)",
    "e4 e5": "Offenes Spiel (1.e4 e5)",
    "e4 e5 Nf3": "Koenigsspringer-Eroeffnung",
    "e4 e5 Nf3 Nc6": "Koenigsspringer, Nc6",
    "e4 e5 Nf3 Nc6 Bc4": "Italienische Partie",
    "e4 e5 Nf3 Nc6 Bc4 Bc5": "Giuoco Piano (Italienisch)",
    "e4 e5 Nf3 Nc6 Bc4 Bc5 c3": "Giuoco Piano, c3",
    "e4 e5 Nf3 Nc6 Bc4 Bc5 d3": "Giuoco Pianissimo",
    "e4 e5 Nf3 Nc6 Bc4 Bc5 Nc3": "Giuoco Pianissimo, Nc3",
    "e4 e5 Nf3 Nc6 Bc4 Bc5 O-O": "Giuoco Piano, O-O",
    "e4 e5 Nf3 Nc6 Bc4 Bc5 b4": "Evans-Gambit",
    "e4 e5 Nf3 Nc6 Bc4 Bc5 Bxf7+": "Jerome-Gambit (unsolide)",
    "e4 e5 Nf3 Nc6 Bc4 Nf6": "Zweispringerspiel im Nachzug",
    "e4 e5 Nf3 Nc6 Bc4 Nf6 d3": "Zweispringerspiel, d3",
    "e4 e5 Nf3 Nc6 Bc4 Nf6 Nc3": "Italienisches Vierspringerspiel",
    "e4 e5 Nf3 Nc6 Bc4 Nf6 Nc3 Bb4": "Italienisches Vierspringerspiel, Bb4",
    "e4 e5 Nf3 Nc6 Bc4 Nf6 d4": "Zweispringerspiel, d4",
    "e4 e5 Nf3 Nc6 Bc4 Nf6 Ng5": "Zweispringerspiel, Ng5 (Fried-Liver-Drohung)",
    "e4 e5 Nf3 Nc6 Bc4 Nf6 Ng5 d5": "Zweispringerspiel, Ng5 d5",
    "e4 e5 Nf3 Nc6 Bc4 Nf6 Ng5 d5 exd5 Nxd5": "Zweispringerspiel, Nxd5 (riskant)",
    "e4 e5 Nf3 Nc6 Bc4 Nf6 Ng5 d5 exd5 Nxd5 Nxf7": "Fried Liver Attack",
    "e4 e5 Nf3 Nc6 Bc4 Nf6 Ng5 d5 exd5 Na5": "Zweispringerspiel, Polerio-Verteidigung (Na5)",
    "e4 e5 Nf3 Nc6 Bc4 Nf6 Ng5 Bc5": "Traxler-Gegenangriff",
    "e4 e5 Nf3 Nc6 Bc4 h6": "Italienisch, Anti-Fried-Liver (h6)",
    "e4 e5 Nf3 Nc6 Bc4 Be7": "Ungarische Verteidigung",
    "e4 e5 Nf3 Nc6 Bc4 d6": "Italienisch, d6",
    "e4 e5 Nf3 Nc6 Bc4 Nd4": "Blackburne-Shilling-Gambit",
    "e4 e5 Nf3 Nc6 Bb5": "Spanisch (Ruy Lopez)",
    "e4 e5 Nf3 Nc6 Bb5 a6": "Spanisch, Morphy-Verteidigung",
    "e4 e5 Nf3 Nc6 Bb5 a6 Ba4": "Spanisch, Hauptlinie",
    "e4 e5 Nf3 Nc6 Bb5 a6 Bxc6": "Spanisch, Abtauschvariante",
    "e4 e5 Nf3 Nc6 Bb5 Nf6": "Spanisch, Berliner Verteidigung",
    "e4 e5 Nf3 Nc6 d4": "Schottisch",
    "e4 e5 Nf3 Nc6 d4 exd4 Nxd4": "Schottisch, Hauptlinie",
    "e4 e5 Nf3 Nc6 d4 exd4 Bc4": "Schottisches Gambit",
    "e4 e5 Nf3 Nc6 d4 exd4 c3": "Goering-Gambit",
    "e4 e5 Nf3 Nc6 Nc3": "Dreispringerspiel",
    "e4 e5 Nf3 Nc6 Nc3 Nf6": "Vierspringerspiel",
    "e4 e5 Nf3 Nc6 Nc3 Nf6 Bc4": "Vierspringerspiel, Italienische Variante",
    "e4 e5 Nf3 Nc6 Nc3 Nf6 Bc4 Bb4": "Vierspringerspiel, Italienisch mit Bb4",
    "e4 e5 Nf3 Nc6 Nc3 Nf6 Bb5": "Vierspringerspiel, Spanische Variante",
    "e4 e5 Nf3 Nc6 Nc3 Nf6 d4": "Schottisches Vierspringerspiel",
    "e4 e5 Nf3 Nf6": "Russisch (Petroff)",
    "e4 e5 Nf3 d6": "Philidor-Verteidigung",
    "e4 e5 Nf3 f5": "Lettisches Gambit",
    "e4 e5 Nc3": "Wiener Partie",
    "e4 e5 Nc3 Nf6 f4": "Wiener Gambit",
    "e4 e5 Nc3 Nc6 Bc4": "Wiener Partie, Bc4",
    "e4 e5 f4": "Koenigsgambit",
    "e4 e5 f4 exf4": "Angenommenes Koenigsgambit",
    "e4 e5 f4 d5": "Falkbeer-Gegengambit",
    "e4 e5 f4 Bc5": "Abgelehntes Koenigsgambit, Bc5",
    "e4 e5 Bc4": "Laeuferspiel",
    "e4 e5 Bc4 Nf6": "Laeuferspiel, Berliner Verteidigung",
    "e4 e5 d4": "Mittelgambit",
    "e4 e5 d4 exd4 Qxd4": "Mittelgambit, Qxd4",
    "e4 e5 d4 exd4 c3": "Daenisches Gambit",
    "e4 e5 Qh5": "Parham-Angriff (Wayward Queen)",
    "e4 e5 Qh5 Nc6 Bc4 g6": "Parham-Angriff, g6 (korrekte Abwehr)",
    "e4 e5 Qh5 Nc6 Bc4 Nf6": "Parham-Angriff, Nf6?? (Schaefermatt droht)",
    "e4 c5": "Sizilianisch",
    "e4 c5 Nf3": "Sizilianisch, Nf3",
    "e4 c5 Nf3 d6 d4": "Offenes Sizilianisch",
    "e4 c5 Nf3 d6 d4 cxd4 Nxd4 Nf6 Nc3 a6": "Sizilianisch, Najdorf",
    "e4 c5 Nf3 d6 d4 cxd4 Nxd4 Nf6 Nc3 g6": "Sizilianisch, Drachen",
    "e4 c5 Nf3 Nc6": "Sizilianisch, Nc6",
    "e4 c5 Nf3 Nc6 Bb5": "Sizilianisch, Rossolimo",
    "e4 c5 Nf3 d6 Bb5+": "Sizilianisch, Moskauer Variante",
    "e4 c5 Nf3 e6": "Sizilianisch, e6",
    "e4 c5 c3": "Alapin-Sizilianisch",
    "e4 c5 Nc3": "Geschlossenes Sizilianisch",
    "e4 c5 Nc3 Nc6 f4": "Grand-Prix-Angriff",
    "e4 c5 f4": "Grand-Prix-Angriff",
    "e4 c5 d4": "Smith-Morra-Gambit",
    "e4 c5 d4 cxd4 c3": "Smith-Morra-Gambit",
    "e4 c5 b4": "Sizilianisch, Fluegelgambit",
    "e4 e6": "Franzoesisch",
    "e4 e6 d4 d5": "Franzoesisch",
    "e4 e6 d4 d5 e5": "Franzoesisch, Vorstossvariante",
    "e4 e6 d4 d5 exd5": "Franzoesisch, Abtauschvariante",
    "e4 e6 d4 d5 Nc3": "Franzoesisch, Nc3",
    "e4 e6 d4 d5 Nc3 Bb4": "Franzoesisch, Winawer",
    "e4 e6 d4 d5 Nc3 Nf6": "Franzoesisch, Klassisch",
    "e4 e6 d4 d5 Nd2": "Franzoesisch, Tarrasch",
    "e4 c6": "Caro-Kann",
    "e4 c6 d4 d5 e5": "Caro-Kann, Vorstossvariante",
    "e4 c6 d4 d5 exd5": "Caro-Kann, Abtauschvariante",
    "e4 c6 d4 d5 Nc3": "Caro-Kann, Hauptlinie",
    "e4 d5": "Skandinavisch",
    "e4 d5 exd5 Qxd5": "Skandinavisch, Qxd5",
    "e4 d5 exd5 Qxd5 Nc3 Qa5": "Skandinavisch, Qa5",
    "e4 d5 exd5 Qxd5 Nc3 Qd8": "Skandinavisch, Qd8",
    "e4 d5 exd5 Qxd5 Nc3 Qd6": "Skandinavisch, Qd6",
    "e4 d5 exd5 Nf6": "Skandinavisch, Nf6",
    "e4 Nf6": "Aljechin-Verteidigung",
    "e4 d6": "Pirc-Verteidigung",
    "e4 g6": "Moderne Verteidigung",
    "e4 Nc6": "Nimzowitsch-Verteidigung",
    "e4 b6": "Owen-Verteidigung",
    "e4 a6": "St.-George-Verteidigung",
    "d4": "Damenbauer (1.d4)",
    "d4 d5": "Damenbauernspiel",
    "d4 d5 c4": "Damengambit",
    "d4 d5 c4 e6": "Abgelehntes Damengambit",
    "d4 d5 c4 e6 Nc3 Nf6": "Abgelehntes Damengambit, Hauptlinie",
    "d4 d5 c4 c6": "Slawisch",
    "d4 d5 c4 c6 Nf3 Nf6 Nc3 dxc4": "Slawisch, Hauptlinie",
    "d4 d5 c4 dxc4": "Angenommenes Damengambit",
    "d4 d5 c4 e5": "Albins Gegengambit",
    "d4 d5 c4 Nc6": "Tschigorin-Verteidigung",
    "d4 d5 c4 Nf6": "Damengambit, Marshall-Verteidigung",
    "d4 d5 Nf3": "Damenbauernspiel, Nf3",
    "d4 d5 Nf3 Nf6 c4": "Damengambit",
    "d4 d5 Nf3 Nf6 c4 e6": "Abgelehntes Damengambit",
    "d4 d5 Nf3 Nf6 e3": "Colle-System",
    "d4 d5 Bf4": "Londoner System",
    "d4 d5 Bf4 Nf6 e3": "Londoner System",
    "d4 d5 Nf3 Nf6 Bf4": "Londoner System",
    "d4 d5 Nf3 Nf6 Bf4 e6": "Londoner System",
    "d4 d5 Nf3 Nf6 Bf4 c5": "Londoner System, c5",
    "d4 Nf6 Bf4": "Londoner System",
    "d4 Nf6 Nf3 g6 Bf4": "Londoner System gegen Koenigsindisch",
    "d4 d5 Nc3": "Veresov / Jobava-London",
    "d4 d5 Nc3 Nf6 Bf4": "Jobava-London",
    "d4 d5 Nc3 Nf6 Bg5": "Veresov-Eroeffnung",
    "d4 d5 e3": "Damenbauer, e3 (Stonewall-Richtung)",
    "d4 Nf6": "Indische Verteidigung",
    "d4 Nf6 c4": "Indisch, c4",
    "d4 Nf6 c4 e6": "Indisch, e6",
    "d4 Nf6 c4 e6 Nc3 Bb4": "Nimzo-Indisch",
    "d4 Nf6 c4 e6 Nf3 b6": "Damenindisch",
    "d4 Nf6 c4 g6": "Koenigsindisch / Gruenfeld",
    "d4 Nf6 c4 g6 Nc3 d5": "Gruenfeld-Indisch",
    "d4 Nf6 c4 g6 Nc3 Bg7": "Koenigsindisch",
    "d4 Nf6 c4 c5": "Benoni",
    "d4 Nf6 c4 c5 d5 b5": "Wolga-Benkoe-Gambit",
    "d4 Nf6 c4 e5": "Budapester Gambit",
    "d4 Nf6 Bg5": "Trompowsky-Angriff",
    "d4 Nf6 Nf3 e6 Bg5": "Torre-Angriff",
    "d4 f5": "Hollaendisch",
    "d4 e5": "Englund-Gambit",
    "d4 d6": "Alt-Indisch",
    "d4 g6": "Moderne Verteidigung (1.d4)",
    "d4 e6": "Damenbauer, e6",
    "d4 c5": "Alt-Benoni",
    "c4": "Englische Eroeffnung",
    "c4 e5": "Englisch, Umgekehrt-Sizilianisch",
    "c4 c5": "Englisch, Symmetrisch",
    "c4 Nf6": "Englisch, Nf6",
    "Nf3": "Reti-Eroeffnung",
    "Nf3 d5 g3": "Reti, Koenigsfianchetto",
    "Nf3 d5 c4": "Reti-Eroeffnung",
    "Nf3 Nf6": "Reti, Nf6",
    "f4": "Bird-Eroeffnung",
    "b3": "Larsen-Eroeffnung",
    "g3": "Koenigsfianchetto-Eroeffnung",
}


# ---------------------------------------------------------------------------
# Bewertung
# ---------------------------------------------------------------------------
def win_prob(score_pov, cap=1000):
    """Gewinnchance 0..100 aus Sicht der Seite, fuer die der PovScore gilt (Lichess Formel).
    Mate(0) = ich bin matt -> 0, MateGiven = ich habe matt gesetzt -> 100 (beide haben mate() == 0)."""
    if score_pov.is_mate():
        return 100.0 if score_pov.score(mate_score=100000) > 0 else 0.0
    cp = max(-cap, min(cap, score_pov.score()))
    return 50 + 50 * (2 / (1 + math.exp(-0.00368208 * cp)) - 1)


def accuracy_from_drop(drop):
    drop = max(0.0, drop)
    return max(0.0, min(100.0, 103.1668 * math.exp(-0.04354 * drop) - 3.1669))


def fmt_score(score_white):
    if score_white.is_mate():
        m = score_white.mate()
        return f"#{m}" if m > 0 else f"#-{abs(m)}"
    return f"{score_white.score() / 100:+.2f}"


def classify(drop, cp_loss):
    """Nur der Verlust an Gewinnchance zaehlt. Centipawns nur fuer BEST/GUT gegen OK."""
    if drop >= 20:
        return "BLUNDER"
    if drop >= 10:
        return "FEHLER"
    if drop >= 5:
        return "UNGENAU"
    return "BEST/GUT" if cp_loss <= 10 else "OK"


def non_pawn_material(board):
    return sum(len(board.pieces(pt, c)) * PIECE_VAL[pt]
               for pt in (chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN) for c in (chess.WHITE, chess.BLACK))


def phase_of(board, fullmove):
    if fullmove <= 10:
        return "Eroeffnung"
    return "Endspiel" if non_pawn_material(board) <= 20 else "Mittelspiel"


def clock_of(node):
    m = re.search(r"\[%clk\s+([\d:.]+)\]", node.comment or "")
    return m.group(1) if m else None


def clock_secs(txt):
    """'0:09:58.1' -> 598.1"""
    if not txt:
        return None
    parts = [float(x) for x in txt.split(":")]
    while len(parts) < 3:
        parts.insert(0, 0.0)
    return parts[0] * 3600 + parts[1] * 60 + parts[2]


def time_control(tc):
    """chess.com TimeControl: '600' oder '600+5' -> (Basis, Inkrement) in Sekunden; Daily ('1/86400') -> None"""
    m = re.fullmatch(r"(\d+)(?:\+(\d+))?", tc or "")
    return (int(m.group(1)), int(m.group(2) or 0)) if m else None


def detect_opening(san_moves):
    best, seq = None, ""
    for i, san in enumerate(san_moves[:14]):
        seq = (seq + " " + san).strip()
        if seq in OPENINGS:
            best = (i + 1, OPENINGS[seq])
    return best


def sparkline(values):
    blocks = "▁▂▃▄▅▆▇█"
    return "".join(blocks[min(7, max(0, int(v / 100 * 8)))] for v in values)


# ---------------------------------------------------------------------------
# Statische Brettpruefung (Stufe 1: Captures). Heuristik, wird mit der Engine abgeglichen.
# ---------------------------------------------------------------------------
def see(board, sq):
    """Statischer Abtausch auf sq (ohne Roentgen): Materialgewinn fuer den Angreifer der Figur auf sq.
    > 0 heisst: die Figur ist gratis oder mit Gewinn schlagbar."""
    victim = board.piece_at(sq)
    if victim is None:
        return 0
    b = board.copy()
    side = not victim.color

    def val(s):
        p = b.piece_at(s)
        return 100 if p.piece_type == chess.KING else PIECE_VAL[p.piece_type]
    gain = [PIECE_VAL[victim.piece_type]]
    last_attacker_val = None
    while True:
        atts = list(b.attackers(side, sq))
        if not atts:
            break
        a = min(atts, key=val)
        if b.piece_at(a).piece_type == chess.KING and b.attackers(not side, sq):
            break  # Koenig schlaegt nicht auf ein gedecktes Feld
        if last_attacker_val is not None:
            gain.append(last_attacker_val - gain[-1])
        last_attacker_val = val(a)
        b.set_piece_at(sq, b.piece_at(a)); b.remove_piece_at(a)
        side = not side
    if last_attacker_val is not None:
        gain.append(last_attacker_val - gain[-1])  # Abschluss: letzter Angreifer koennte noch geschlagen werden (Wert als Risiko)
        gain.pop()  # ... aber niemand kann mehr schlagen, also weg damit
    for d in range(len(gain) - 1, 0, -1):
        gain[d - 1] = -max(-gain[d - 1], gain[d])
    return gain[0]


def en_prise(board, color):
    """Figuren von color (ohne Koenig), die der Gegner laut statischem Abtausch mit Gewinn schlagen kann."""
    out = {}
    for sq, pc in board.piece_map().items():
        if pc.color != color or pc.piece_type == chess.KING or not board.attackers(not color, sq):
            continue
        if see(board, sq) > 0:
            out[sq] = "ungedeckt" if not board.attackers(color, sq) else "zu schwach gedeckt"
    return out


def fork_targets(board_after_reply, sq, user_color):
    """Was greift die Figur auf sq an, das wertvoller ist als sie selbst (oder der Koenig)?"""
    p = board_after_reply.piece_at(sq)
    if p is None or p.piece_type == chess.KING:
        return []
    t = []
    for s in board_after_reply.attacks(sq):
        v = board_after_reply.piece_at(s)
        if v is not None and v.color == user_color and (v.piece_type == chess.KING or PIECE_VAL[v.piece_type] > PIECE_VAL[p.piece_type]):
            t.append(PIECE_DE[v.piece_type] + " " + chess.square_name(s))
    return t


def stufe1_facts(b_before, move, b_after, best_move, best_reply, user_color):
    """Liefert fuer einen eigenen Zug: was haengt danach neu (vom Gegner per bestem Zug schlagbar),
    was stand vorher gratis (bester Zug war genau dieses Schlagen), habe ich gratis genommen."""
    f = {"haengt_neu": [], "haengt_nicht_gerettet": [], "gratis_vorher": [], "gratis_genommen": False, "gratis_liegen_gelassen": False}
    before = en_prise(b_before, user_color)
    opp_free = en_prise(b_before, not user_color)
    if opp_free:
        if b_before.is_capture(move) and move.to_square in opp_free:
            f["gratis_genommen"] = True
        elif best_move is not None and b_before.is_capture(best_move) and best_move.to_square in opp_free:
            f["gratis_liegen_gelassen"] = True
            f["gratis_vorher"] = [f"{PIECE_DE[b_before.piece_at(s).piece_type]} {chess.square_name(s)}" for s in opp_free]
    after = en_prise(b_after, user_color)
    if best_reply is not None and b_after.is_capture(best_reply) and best_reply.to_square in after:
        s = best_reply.to_square
        txt = f"{PIECE_DE[b_after.piece_at(s).piece_type]} {chess.square_name(s)} ({after[s]}, {PIECE_DE[b_after.piece_at(best_reply.from_square).piece_type]} schlaegt)"
        if s not in before or s == move.to_square:
            f["haengt_neu"] = [txt]                       # neu hingestellt oder stehen gelassen und jetzt angreifbar
        else:
            f["haengt_nicht_gerettet"] = [txt + ", hing schon vorher"]   # Blick 2 vergessen: Figur war angegriffen, nicht gerettet
    return f


def drill_stufe(b_before, move, b_after, best_move, best_reply, facts, user_color, score_before_pov, score_after_pov):
    """Welche Stufe trainiert diese Stellung? 1 Captures, 2 Checks, 3 Attacks (Gabel), 0 = kein Drill (positionell)."""
    if facts["haengt_neu"]:
        return 1, "Captures: Figur haengen lassen"
    if facts["gratis_liegen_gelassen"]:
        return 1, "Captures: gratis Material liegen gelassen"
    if facts["haengt_nicht_gerettet"]:
        return 1, "Captures: angegriffene Figur nicht gerettet"
    if best_move is not None and b_before.gives_check(best_move):
        if score_before_pov.is_mate() and score_before_pov.mate() > 0:
            return 2, "Checks: Matt uebersehen"
        return 2, "Checks: bester Zug war ein Schach"
    if score_after_pov.is_mate() and score_after_pov.mate() < 0 and not (score_before_pov.is_mate() and score_before_pov.mate() < 0):
        return 2, "Checks: Matt zugelassen"
    if best_reply is not None and b_after.gives_check(best_reply) and b_after.is_capture(best_reply):
        return 2, "Checks: Schach mit Materialgewinn zugelassen"
    if best_reply is not None:
        b2 = b_after.copy(); b2.push(best_reply)
        t = fork_targets(b2, best_reply.to_square, user_color)
        if len(t) >= 2:
            return 3, f"Attacks: Gabel auf {', '.join(t)}"
    return 0, "positionell"


# ---------------------------------------------------------------------------
# Engine Pool
# ---------------------------------------------------------------------------
class Pool:
    def __init__(self, n):
        self.engines = []
        for _ in range(n):
            e = chess.engine.SimpleEngine.popen_uci(ENGINE_PATH)
            e.configure({"Threads": 1, "Hash": HASH_MB})
            self.engines.append(e)

    @staticmethod
    def evaluate(engine, board, depth, multipv=1):
        if board.is_game_over():
            sc = chess.engine.Mate(0) if board.is_checkmate() else chess.engine.Cp(0)
            return [{"score": chess.engine.PovScore(sc, board.turn), "pv": []}]
        info = engine.analyse(board, chess.engine.Limit(depth=depth), multipv=multipv)
        if isinstance(info, dict):
            info = [info]
        return [{"score": i["score"], "pv": i.get("pv", [])} for i in info]

    def run(self, jobs):
        """jobs: Liste (board, depth, multipv). Zusammenhaengende Bloecke je Engine (Hash bleibt warm). Reihenfolge bleibt."""
        n = len(self.engines)
        if not jobs:
            return []
        chunk = (len(jobs) + n - 1) // n
        parts = [jobs[i:i + chunk] for i in range(0, len(jobs), chunk)]

        def work(k):
            return [self.evaluate(self.engines[k], *j) for j in parts[k]]
        with ThreadPoolExecutor(max_workers=len(parts)) as ex:
            res = list(ex.map(work, range(len(parts))))
        return [r for part in res for r in part]

    def quit(self):
        for e in self.engines:
            e.quit()


# ---------------------------------------------------------------------------
# Hauptanalyse
# ---------------------------------------------------------------------------
def analyze_game(pgn_text, player=PLAYER, quiet=False):
    game = chess.pgn.read_game(io.StringIO(pgn_text))
    if game is None:
        raise SystemExit("Konnte PGN nicht lesen.")
    hdr = game.headers
    white, black = hdr.get("White", "?"), hdr.get("Black", "?")
    if player.lower() == white.lower():
        user_color = chess.WHITE
    elif player.lower() == black.lower():
        user_color = chess.BLACK
    else:
        raise SystemExit(f"Spieler {player} ist weder Weiss ({white}) noch Schwarz ({black}).")

    nodes = list(game.mainline())
    boards = [game.board()]
    for n in nodes:
        b = boards[-1].copy(); b.push(n.move); boards.append(b)

    pool = Pool(N_WORKERS)
    log = (lambda *a: None) if quiet else (lambda *a: print(*a, file=sys.stderr, flush=True))
    log(f"Stockfish: {len(boards)} Stellungen, Tiefe {DEPTH_FAST}, {N_WORKERS} Engines ...")
    evals = pool.run([(b, DEPTH_FAST, 1) for b in boards])
    evals = [e[0] for e in evals]

    tc = time_control(hdr.get("TimeControl"))
    last_clock = {chess.WHITE: tc[0] if tc else None, chess.BLACK: tc[0] if tc else None}

    moves_out = []
    stats = {c: {"acc": [], "cpl": [], "cls": {}, "phase_cpl": {"Eroeffnung": [], "Mittelspiel": [], "Endspiel": []}}
             for c in (chess.WHITE, chess.BLACK)}
    win_curve = []
    kpi = {"haengen_gelassen": 0, "haengen_bestraft": 0, "gratis_liegen_gelassen": 0, "gratis_genommen": 0}

    for i, node in enumerate(nodes):
        b_before, b_after = boards[i], boards[i + 1]
        mover, move = b_before.turn, node.move
        fullmove = b_before.fullmove_number
        before_pov = evals[i]["score"].pov(mover)
        after_pov = evals[i + 1]["score"].pov(mover)
        wp_before, wp_after = win_prob(before_pov), win_prob(after_pov)
        drop = wp_before - wp_after
        cp_loss = max(0, before_pov.score(mate_score=10000) - after_pov.score(mate_score=10000))
        best_move = evals[i]["pv"][0] if evals[i]["pv"] else None
        best_reply = evals[i + 1]["pv"][0] if evals[i + 1]["pv"] else None
        if best_move == move:
            cls, cp_loss, drop = "BEST", 0, max(0.0, drop)
        else:
            cls = classify(drop, cp_loss)
        acc = accuracy_from_drop(drop)
        phase = phase_of(b_before, fullmove)
        st = stats[mover]
        st["acc"].append(acc); st["cpl"].append(min(cp_loss, 1000))
        st["cls"][cls] = st["cls"].get(cls, 0) + 1
        st["phase_cpl"][phase].append(min(cp_loss, 1000))

        entry = {
            "ply": i + 1, "move_no": f"{fullmove}." if mover == chess.WHITE else f"{fullmove}...",
            "mover": "user" if mover == user_color else "opp", "san": b_before.san(move),
            "eval_before": fmt_score(evals[i]["score"].white()), "eval_after": fmt_score(evals[i + 1]["score"].white()),
            "win_before": round(wp_before, 1), "win_after": round(wp_after, 1), "drop": round(drop, 1),
            "cp_loss": int(cp_loss), "class": cls, "best": b_before.san(best_move) if best_move else None,
            "phase": phase, "clock": clock_of(node), "fen_before": b_before.fen(),
        }
        now = clock_secs(entry["clock"])
        if tc and now is not None and last_clock[mover] is not None:
            entry["secs"] = round(max(0.0, last_clock[mover] - now + tc[1]), 1)
        if now is not None:
            last_clock[mover] = now
        if mover == user_color:
            win_curve.append(round(wp_after))
            facts = stufe1_facts(b_before, move, b_after, best_move, best_reply, user_color)
            if facts["haengt_neu"] and drop >= 10:
                kpi["haengen_gelassen"] += 1
                if i + 1 < len(nodes) and b_after.is_capture(nodes[i + 1].move) and nodes[i + 1].move.to_square == best_reply.to_square:
                    kpi["haengen_bestraft"] += 1
            else:
                facts["haengt_neu"] = []  # ohne Engine Verlust kein Haengen (Abtausch)
            if drop < 10:
                facts["haengt_nicht_gerettet"] = []
            if facts["gratis_liegen_gelassen"] and drop >= 10:
                kpi["gratis_liegen_gelassen"] += 1
            else:
                facts["gratis_liegen_gelassen"] = False; facts["gratis_vorher"] = []
            if facts["gratis_genommen"]:
                kpi["gratis_genommen"] += 1
            stufe, grund = drill_stufe(b_before, move, b_after, best_move, best_reply, facts, user_color, before_pov, after_pov)
            entry["stufe1"] = facts
            entry["drill_stufe"] = stufe if (drop >= DRILL_MIN_DROP and cls != "BEST") else 0
            entry["drill_grund"] = grund if entry["drill_stufe"] else ""
        moves_out.append(entry)

    # Lektions- und Drillkandidaten: die 3 schwersten eigenen Fehler plus alle Drillkandidaten (max 6)
    user_bad = [m for m in moves_out if m["mover"] == "user" and m["class"] in ("BLUNDER", "FEHLER")]
    user_bad.sort(key=lambda m: -m["drop"])
    chosen, seen = [], set()
    for m in user_bad[:3] + [m for m in user_bad if m["drill_stufe"]]:
        if m["ply"] not in seen and len(chosen) < 6:
            chosen.append(m); seen.add(m["ply"])
    chosen.sort(key=lambda m: -m["drop"])
    if chosen:
        log(f"Tiefenanalyse {len(chosen)} Stellungen (Tiefe {DEPTH_DEEP}, 3 Varianten) ...")
        deep = pool.run([(boards[m["ply"] - 1], DEPTH_DEEP, 3) for m in chosen] + [(boards[m["ply"]], DEPTH_PUNISH, 1) for m in chosen])
        for k, m in enumerate(chosen):
            b_before, b_after = boards[m["ply"] - 1], boards[m["ply"]]
            lines, after_deep = deep[k], deep[len(chosen) + k][0]
            best_pv = lines[0]["pv"]
            best_move = best_pv[0] if best_pv else None
            m["best"] = b_before.san(best_move) if best_move else m["best"]
            m["best_line"] = b_before.variation_san(best_pv[:6]) if best_pv else ""
            m["eval_best"] = fmt_score(lines[0]["score"].white())
            w_best = win_prob(lines[0]["score"].pov(b_before.turn))
            m["win_best"] = round(w_best, 1)
            m["accepted"] = [b_before.san(l["pv"][0]) for l in lines if l["pv"] and w_best - win_prob(l["score"].pov(b_before.turn)) <= ALT_WINDOW]
            m["alternatives"] = [(b_before.san(l["pv"][0]), fmt_score(l["score"].white())) for l in lines[1:] if l["pv"]]
            reply_pv = after_deep["pv"]
            m["punish_line"] = b_after.variation_san(reply_pv[:6]) if reply_pv else ""
            if m["ply"] < len(nodes):
                actual = nodes[m["ply"]].move
                m["opp_reply_actual"] = b_after.san(actual)
                m["opp_punished"] = bool(reply_pv) and actual == reply_pv[0]

    # Lektion 1 und 2: erst Stellungen der aktuellen Stufe (oder darunter) nach Verlust, dann alle anderen nach Verlust
    recent = set()
    for g in load_progress()["games"][-5:]:
        recent.update(g.get("lektionen", []))

    def pattern(m):
        return m["drill_grund"].split(" (")[0] if m["drill_stufe"] else "positionell"

    def lesson_key(m):
        st = m["drill_stufe"]
        return (0 if 0 < st <= STUFE else 1, 0 if pattern(m) in recent else 1, -m["drop"])
    ordered = sorted(chosen, key=lesson_key)
    lessons = ordered[:1]
    for m in ordered[1:]:  # Lektion 2: ein anderes Muster als Lektion 1, sonst der naechste nach Verlust
        if pattern(m) != pattern(lessons[0]):
            lessons.append(m); break
    if len(lessons) < 2 and len(ordered) > 1:
        lessons.append(ordered[1])
    for m in lessons:
        m["wiederholung"] = pattern(m) in recent

    # Funde: eigene BEST Zuege in offener Stellung, Abstand zum zweitbesten Zug (Tiefe 16, 2 Varianten)
    def trivial(m):  # Rueckschlag auf dem Feld des letzten Gegnerzugs oder Zug im Schach = kein Fund
        b = boards[m["ply"] - 1]
        mv = b.parse_san(m["san"])
        prev = nodes[m["ply"] - 2].move if m["ply"] >= 2 else None
        return b.is_check() or mv.promotion is not None or (prev is not None and boards[m["ply"] - 2].is_capture(prev) and prev.to_square == mv.to_square)
    cand = [m for m in moves_out if m["mover"] == "user" and m["class"] == "BEST" and 10 <= m["win_before"] <= 90 and not trivial(m)]
    finds = []
    if cand:
        log(f"Funde: {len(cand)} eigene beste Zuege mit 2 Varianten ...")
        res = pool.run([(boards[m["ply"] - 1], DEPTH_FAST, 2) for m in cand])
        for m, lines in zip(cand, res):
            if len(lines) < 2 or not lines[1]["pv"]:
                continue
            b = boards[m["ply"] - 1]
            w1 = win_prob(lines[0]["score"].pov(b.turn)); w2 = win_prob(lines[1]["score"].pov(b.turn))
            mv = b.parse_san(m["san"])
            finds.append({"move_no": m["move_no"], "san": m["san"], "gap": round(w1 - w2, 1), "second": b.san(lines[1]["pv"][0]),
                          "taktisch": b.is_capture(mv) or b.gives_check(mv), "fen": m["fen_before"],
                          "line": b.variation_san(lines[0]["pv"][:6]), "win_best": round(w1), "win_second": round(w2)})
    finds = [f for f in finds if f["gap"] >= 5]
    best_find = max([f for f in finds if f["taktisch"]], key=lambda f: f["gap"], default=None)
    hard_find = max([f for f in finds if not f["taktisch"]], key=lambda f: f["gap"], default=None)

    # Verpasste Chancen: Gegner patzt, eigener Antwortzug nicht gut
    missed, opp_bad = [], 0
    for i, m in enumerate(moves_out[:-1]):
        nxt = moves_out[i + 1]
        if m["mover"] == "opp" and m["class"] in ("BLUNDER", "FEHLER"):
            opp_bad += 1
            if nxt["mover"] == "user" and nxt["class"] in ("BLUNDER", "FEHLER", "UNGENAU"):
                missed.append({"after_opp_move": f"{m['move_no']} {m['san']}", "you_played": f"{nxt['move_no']} {nxt['san']}",
                               "best": nxt["best"], "win_before": nxt["win_before"], "win_after": nxt["win_after"], "fen": nxt["fen_before"]})
    pool.quit()

    def side_summary(color):
        st = stats[color]; n = max(1, len(st["acc"]))
        mean_acc = sum(st["acc"]) / n
        harm_acc = n / sum(1 / max(1.0, a) for a in st["acc"]) if st["acc"] else 0.0
        return {"accuracy": round((mean_acc + harm_acc) / 2, 1), "acpl": round(sum(st["cpl"]) / n), "moves": len(st["acc"]),
                "classes": st["cls"], "phase_acpl": {k: (round(sum(v) / len(v)) if v else None) for k, v in st["phase_cpl"].items()},
                "phase_moves": {k: len(v) for k, v in st["phase_cpl"].items()}}

    san_list = [m["san"] for m in moves_out]
    opening = detect_opening(san_list)
    result = hdr.get("Result", "*")
    user_result = "Remis" if result == "1/2-1/2" else (
        "Sieg" if (result == "1-0" and user_color == chess.WHITE) or (result == "0-1" and user_color == chess.BLACK) else
        ("Niederlage" if result in ("1-0", "0-1") else "?"))
    user_moves = [m for m in moves_out if m["mover"] == "user"]
    turning = max(user_moves, key=lambda m: m["drop"]) if user_moves else None
    kpi["gegner_patzer"] = opp_bad
    kpi["gegner_patzer_genutzt"] = opp_bad - len(missed)
    # Koenigssicherheit (Schicht 0): wann rochiert, und steht der Koenig nach Zug 12 noch in der Mitte, waehrend seine Dame lebt?
    roch = next((boards[i].fullmove_number for i, nd in enumerate(nodes) if boards[i].turn == user_color and boards[i].is_castling(nd.move)), None)
    kpi["rochade_zug"] = roch
    b12 = next((b for b in boards if b.fullmove_number >= 13 and b.turn == chess.WHITE), None)
    kpi["koenig_zentrum"] = bool(b12 is not None and (roch is None or roch > 12) and b12.king(user_color) in (chess.E1, chess.E8) and b12.pieces(chess.QUEEN, not user_color))
    secs = sorted(m["secs"] for m in user_moves if "secs" in m)
    if secs:
        kpi["sek_median"] = secs[len(secs) // 2]
        kpi["blunder_schnell"] = sum(1 for m in user_moves if m["class"] == "BLUNDER" and m.get("secs", 99) < 5)
        kpi["blunder_gesamt"] = sum(1 for m in user_moves if m["class"] == "BLUNDER")
    return {
        "date": hdr.get("Date", "?"), "white": white, "black": black,
        "white_elo": hdr.get("WhiteElo", "?"), "black_elo": hdr.get("BlackElo", "?"),
        "time_control": hdr.get("TimeControl", "?"), "result": result,
        "ende": (hdr.get("UTCDate", hdr.get("Date", "?")) + " " + hdr.get("UTCTime", "00:00:00")),
        "user_color": "Weiss" if user_color == chess.WHITE else "Schwarz", "user_result": user_result,
        "opening": {"moves_matched": opening[0], "name": opening[1]} if opening else None,
        "first_moves": " ".join(f"{(k // 2) + 1}.{'' if k % 2 == 0 else '..'}{s}" for k, s in enumerate(san_list[:12])),
        "user": side_summary(user_color), "opp": side_summary(not user_color), "kpi": kpi,
        "win_curve_user": win_curve, "turning_point": turning, "critical": chosen, "lessons": lessons, "missed_chances": missed,
        "best_find": best_find, "hard_find": hard_find, "moves": moves_out,
        "engine": "Stockfish 19", "depth_fast": DEPTH_FAST, "depth_deep": DEPTH_DEEP, "workers": N_WORKERS,
    }


# ---------------------------------------------------------------------------
# Textreport (kurz: Kopf, Kennzahlen, Lektionskandidaten, Funde, Zugliste)
# ---------------------------------------------------------------------------
def text_report(r):
    L = []
    u, o, k = r["user"], r["opp"], r["kpi"]
    L.append("=" * 72)
    L.append(f"ROAD TO 1000 | {r['date']} | {r['white']} ({r['white_elo']}) vs {r['black']} ({r['black_elo']}) | {r['result']} | TC {r['time_control']}")
    L.append(f"{PLAYER} spielt {r['user_color']} -> {r['user_result']} | {r['engine']} Tiefe {r['depth_fast']}/{r['depth_deep']}, {r['workers']} Engines")
    L.append("=" * 72)
    if r["opening"]:
        L.append(f"Eroeffnung: {r['opening']['name']} (erkannt nach {r['opening']['moves_matched']} Halbzuegen)")
    L.append(f"Erste Zuege: {r['first_moves']}")
    L.append(f"Genauigkeit {PLAYER} {u['accuracy']} % (Gegner {o['accuracy']} %) | ACPL {u['acpl']} (Gegner {o['acpl']})")

    def cls_line(c):
        return " | ".join(f"{x} {c.get(x, 0)}" for x in ("BLUNDER", "FEHLER", "UNGENAU", "OK", "BEST/GUT", "BEST"))
    L.append(f"Zuege {PLAYER}: {cls_line(u['classes'])}")
    L.append(f"Zuege Gegner:   {cls_line(o['classes'])}")
    pa, pm = u["phase_acpl"], u["phase_moves"]
    L.append("ACPL je Phase: " + " | ".join(f"{x} {pa[x] if pa[x] is not None else '-'} ({pm[x]} Z.)" for x in ("Eroeffnung", "Mittelspiel", "Endspiel")))
    L.append("")
    L.append(f"STUFE 1 (Captures): haengen gelassen {k['haengen_gelassen']} (vom Gegner bestraft {k['haengen_bestraft']}) | "
             f"gratis liegen gelassen {k['gratis_liegen_gelassen']} | gratis genommen {k['gratis_genommen']} | "
             f"Gegnerpatzer genutzt {k['gegner_patzer_genutzt']} von {k['gegner_patzer']}")
    L.append(f"KOENIG (Schicht 0): Rochade {'in Zug ' + str(k['rochade_zug']) if k.get('rochade_zug') else 'nie'}"
             + (" | Koenig nach Zug 12 noch in der Mitte, seine Dame lebt: JA" if k.get("koenig_zentrum") else ""))
    if "sek_median" in k:
        L.append(f"ZEIT (Uhr aus PGN): Median {k['sek_median']:.0f} s je Zug | Blunder unter 5 Sekunden: {k['blunder_schnell']} von {k['blunder_gesamt']}")
    L.append("Gewinnchance nach jedem eigenen Zug: " + sparkline(r["win_curve_user"]))
    L.append("  " + " ".join(str(v) for v in r["win_curve_user"]))
    if r["turning_point"] and r["turning_point"]["drop"] >= 10:
        t = r["turning_point"]
        L.append(f"Groesster Einbruch: {t['move_no']} {t['san']} ({t['win_before']} % -> {t['win_after']} %)")
    L.append("")
    L.append("-" * 72)
    L.append(f"LEKTION 1 und 2 (automatisch gewaehlt: erst Stufe {STUFE} Stoff, dann groesster Verlust). Bilder L1.png, L2.png")
    L.append("-" * 72)
    for k, m in enumerate(r.get("lessons", []), 1):
        L.append(f"Lektion {k}: {m['move_no']} {m['san']} -> besser {m['best']} | {m['drill_grund'] or 'positionell'}"
                 f"{' | WIEDERHOLUNG (Muster schon in den letzten 5 Partien)' if m.get('wiederholung') else ''} | {m['win_before']:.0f} % -> {m['win_after']:.0f} %")
    L.append("")
    L.append("-" * 72)
    L.append(f"ALLE KANDIDATEN (Tiefe {r['depth_deep']}, nach Schwere). Drill = Stufe der Aufgabe, 0 = positionell, kein Drill")
    L.append("-" * 72)
    if not r["critical"]:
        L.append("Keine Blunder oder Fehler laut Engine. Stark.")
    for n, m in enumerate(r["critical"], 1):
        L.append(f"#{n} {m['move_no']} {m['san']} [{m['class']}] {m['win_before']} % -> {m['win_after']} % | Eval {m['eval_before']} -> {m['eval_after']}"
                 f" | Drill {m['drill_stufe']} {m['drill_grund']}" + (f" | in {m['secs']:.0f} s gespielt, Uhr {m['clock']}" if m.get("secs") is not None else ""))
        L.append(f"   FEN: {m['fen_before']}")
        L.append(f"   Besser: {m['best']} (Eval {m.get('eval_best')}) | auch richtig: {', '.join(m.get('accepted', [])) or '-'}"
                 + (f" | Alternativen: {', '.join(f'{a} ({e})' for a, e in m['alternatives'])}" if m.get("alternatives") else ""))
        if m.get("best_line"):
            L.append(f"   Variante: {m['best_line']}")
        if m.get("punish_line"):
            L.append(f"   Widerlegung nach {m['san']}: {m['punish_line']}" +
                     (f" | Gegner spielte {m['opp_reply_actual']} ({'bestraft' if m['opp_punished'] else 'NICHT bestraft'})" if "opp_reply_actual" in m else ""))
        f = m.get("stufe1", {})
        if f.get("haengt_neu") or f.get("haengt_nicht_gerettet"):
            L.append(f"   Fakt: haengt danach: {', '.join(f['haengt_neu'] + f['haengt_nicht_gerettet'])}")
        if f.get("gratis_liegen_gelassen"):
            L.append(f"   Fakt: stand gratis: {', '.join(f['gratis_vorher'])}")
        L.append("")
    if r["missed_chances"]:
        L.append("-" * 72)
        L.append("VERPASSTE CHANCEN (Gegner patzt, du nutzt es nicht)")
        L.append("-" * 72)
        for mc in r["missed_chances"][:8]:
            L.append(f"Nach {mc['after_opp_move']}: du {mc['you_played']}, besser {mc['best']} ({mc['win_before']} % statt {mc['win_after']} %) | FEN {mc['fen']}")
        L.append("")
    L.append("-" * 72)
    L.append("FUNDE (eigene beste Zuege, Abstand zum zweitbesten Zug in Gewinnchance). Bilder F1.png, F2.png")
    L.append("-" * 72)
    for label, f in (("Bester Fund (taktisch)", r["best_find"]), ("Schwierigster Fund (ruhiger Zug)", r["hard_find"])):
        if f:
            L.append(f"{label}: {f['move_no']} {f['san']} ({f['win_best']} %), zweitbester {f['second']} ({f['win_second']} %), Abstand {f['gap']} | FEN {f['fen']}")
            L.append(f"   Variante: {f['line']}")
        else:
            L.append(f"{label}: keiner mit Abstand >= 5")
    L.append("")
    L.append("-" * 72)
    L.append("ALLE ZUEGE (DU = eigener Zug | Zug | Gewinnchance vorher -> nachher | bester Zug | Klasse)")
    L.append("-" * 72)
    for m in r["moves"]:
        who = "DU " if m["mover"] == "user" else "   "
        flag = "" if m["class"] in ("BEST", "BEST/GUT", "OK") else f" <-- {m['class']}"
        L.append(f"{who}{m['move_no']:>6} {m['san']:<7} {m['win_before']:>5.1f} -> {m['win_after']:>5.1f}  best {m['best'] or '-':<7}{flag}")
    return "\n".join(L)


# ---------------------------------------------------------------------------
# Fortschritt
# ---------------------------------------------------------------------------
def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"player": PLAYER, "goal": 1000, "games": []}


def record_progress(r, game_id):
    p = load_progress()
    p["games"] = [g for g in p["games"] if g["id"] != game_id]  # Neuanalyse ersetzt den alten Eintrag
    opp = r["white"] if r["user_color"] == "Schwarz" else r["black"]
    opp_elo = r["white_elo"] if r["user_color"] == "Schwarz" else r["black_elo"]
    user_elo = r["black_elo"] if r["user_color"] == "Schwarz" else r["white_elo"]
    p["games"].append({
        "id": game_id, "date": r["date"], "ende": r.get("ende", r["date"]), "color": r["user_color"], "opp": opp, "opp_elo": opp_elo, "user_elo": user_elo,
        "result": r["user_result"], "opening": r["opening"]["name"] if r["opening"] else None,
        "accuracy": r["user"]["accuracy"], "acpl": r["user"]["acpl"], "moves": r["user"]["moves"],
        "blunders": r["user"]["classes"].get("BLUNDER", 0), "mistakes": r["user"]["classes"].get("FEHLER", 0),
        "kpi": r["kpi"], "phase_acpl": r["user"]["phase_acpl"],
        "drill_stufen": [m["drill_stufe"] for m in r["critical"] if m["drill_stufe"]],
        "lektionen": [(m["drill_grund"].split(" (")[0] if m["drill_stufe"] else "positionell") for m in r.get("lessons", [])],
        # kompakte Stellungen fuer Konzeptlektionen und Wiederholung, damit alte Reports nicht gebraucht werden
        "stellungen": [{"fen": m["fen_before"], "muster": (m["drill_grund"].split(" (")[0] if m["drill_stufe"] else "positionell"),
                        "zug": m["move_no"], "gespielt": m["san"], "besser": m["best"], "akzeptiert": m.get("accepted", [m["best"]]),
                        "vorher": m["win_before"], "nachher": m["win_after"], "weiss": r["user_color"] == "Weiss"} for m in r["critical"]],
        "worst": [f"{m['move_no']} {m['san']} ({m['class']}, {m['drop']} %)" for m in r["critical"][:3]],
    })
    p["games"].sort(key=lambda g: (g.get("ende", g["date"]), g["id"]))
    with open(PROGRESS_FILE, "w") as f:
        json.dump(p, f, indent=1, ensure_ascii=False)


def show_progress():
    p = load_progress(); g = p["games"]
    if not g:
        print("Noch keine Spiele analysiert."); return
    print(f"ROAD TO 1000 | {len(g)} Spiele | Ziel {p['goal']}")
    print(f"{'#':>2} {'Datum':<10} {'Farbe':<7} {'Elo':>4} {'Gegner':<14} {'GElo':>4} {'Erg':<10} {'Acc':>5} {'Bl':>2} {'Fe':>2} {'Zg':>3} {'Haeng':>5} {'GrLieg':>6} {'GrNimm':>6} {'Patzer':>7} {'Roch':>4} {'Sek':>4}  Eroeffnung")
    for i, x in enumerate(g, 1):
        k = x["kpi"]
        roch = str(k.get("rochade_zug") or "nie") + ("!" if k.get("koenig_zentrum") else "")
        sek = f"{k['sek_median']:.0f}" if "sek_median" in k else "-"
        print(f"{i:>2} {x['date']:<10} {x['color']:<7} {str(x['user_elo']):>4} {str(x.get('opp', '?'))[:14]:<14} {str(x['opp_elo']):>4} {x['result']:<10} {x['accuracy']:>5} "
              f"{x['blunders']:>2} {x['mistakes']:>2} {x['moves']:>3} {k['haengen_gelassen']:>5} {k['gratis_liegen_gelassen']:>6} {k['gratis_genommen']:>6} "
              f"{str(k['gegner_patzer_genutzt']) + '/' + str(k['gegner_patzer']):>7} {roch:>4} {sek:>4}  {x['opening'] or '-'}")
    last = g[-10:]; n = len(last)
    moves = sum(x["moves"] for x in last)
    hang = sum(x["kpi"]["haengen_gelassen"] for x in last)
    gl = sum(x["kpi"]["gratis_liegen_gelassen"] for x in last); gn = sum(x["kpi"]["gratis_genommen"] for x in last)
    pz = sum(x["kpi"]["gegner_patzer"] for x in last); pg = sum(x["kpi"]["gegner_patzer_genutzt"] for x in last)
    bl = sum(x["blunders"] for x in last)
    print()
    bs = sum(x["kpi"].get("blunder_schnell", 0) for x in last); bg = sum(x["kpi"].get("blunder_gesamt", 0) for x in last)
    print(f"LETZTE {n} PARTIEN: Blunder je 40 Zuege {bl * 40 / max(1, moves):.1f} | haengen gelassen je Partie {hang / n:.2f} | "
          f"gratis genommen {gn} von {gn + gl} ({100 * gn / max(1, gn + gl):.0f} %) | Gegnerpatzer genutzt {pg} von {pz} ({100 * pg / max(1, pz):.0f} %)"
          + (f" | Blunder unter 5 s: {bs} von {bg}" if bg else ""))
    print(f"Stufe 2 (Checks) wird frei, wenn ueber 10 Partien: haengen gelassen < 1,0 je Partie UND gratis genommen >= 90 %. "
          f"Jetzt: {hang / n:.2f} und {100 * gn / max(1, gn + gl):.0f} % ueber {n} Partien.")
    from collections import Counter
    pat = Counter(p for x in last for p in x.get("lektionen", []))
    if pat:
        print("Lektionsmuster der letzten Partien: " + ", ".join(f"{k} ({v}x)" for k, v in pat.most_common(5)))
    kz = sum(1 for x in last if x["kpi"].get("koenig_zentrum"))
    print(f"Koenig nach Zug 12 in der Mitte (seine Dame lebt): {kz} von {n} Partien (Roch! in der Tabelle)")
    faellig = [(k, v) for k, v in pat.items() if v >= 3] + ([("Koenigssicherheit", kz)] if kz >= 3 else [])
    for k, v in faellig:
        print(f"KONZEPT FAELLIG: {k} ({v} von {n} Partien). Karte aus KONZEPTE.md plus 3 eigene Stellungen, siehe Protokoll Abschnitt 5a.")
    res = Counter(x["result"] for x in g)
    print("Ergebnisse: " + ", ".join(f"{k} {v}" for k, v in res.items()))


# ---------------------------------------------------------------------------
def main():
    if len(sys.argv) < 2:
        print(__doc__); return
    if sys.argv[1] == "--progress":
        show_progress(); return
    if sys.argv[1] == "--fetch":
        import subprocess, time
        def git(*a):
            return subprocess.run(["git", *a], cwd=BASE, capture_output=True, text=True)
        if git("rev-parse", "--is-inside-work-tree").returncode or "origin" not in git("remote").stdout:
            raise SystemExit("--fetch braucht einen Git Klon des Repos mit Schreibrecht. Rueckfall: python3 analyze.py --pull")
        if not git("config", "user.email").stdout.strip():
            git("config", "user.name", "road1000"); git("config", "user.email", "road1000@users.noreply.github.com")
        branch = git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
        if branch == "HEAD":   # losgeloester Stand: auf main wechseln, sonst geht kein pull
            git("checkout", "-q", "-B", "main", "origin/main"); branch = "main"
        git("pull", "-q", "--rebase", "origin", branch)
        with open(os.path.join(BASE, "request.txt"), "w") as f:
            f.write(datetime.datetime.now().isoformat(timespec="seconds") + "\n")
        git("add", "request.txt")
        r = git("commit", "-qm", "Abruf angefordert")
        if r.returncode:
            raise SystemExit("Commit fehlgeschlagen: " + (r.stdout + r.stderr).strip()[:300])
        r = git("push", "-q", "origin", f"HEAD:{branch}")
        if r.returncode:
            raise SystemExit("Push fehlgeschlagen (kein Schreibrecht? GitHub Konto mlauberg verbunden?): " + r.stderr.strip()[:200] + "\nRueckfall: python3 analyze.py --pull")
        print("[--fetch] Abruf angestossen, warte auf die GitHub Action ...", file=sys.stderr, flush=True)
        path = os.path.join(BASE, "inbox", "alle.pgn")
        marker = os.path.join(BASE, "inbox", ".last_run.txt")   # schreibt die Action bei jedem Lauf, auch ohne neue Partien
        def read(p):
            return open(p, encoding="utf-8").read() if os.path.exists(p) else ""
        old, old_marker = read(path), read(marker)
        deadline = time.time() + int(os.environ.get("FETCH_WAIT", "180"))
        while time.time() < deadline:
            time.sleep(10)
            git("pull", "-q", "--rebase", "origin", branch)
            if read(marker) != old_marker:
                break
        text = read(path)
        if read(marker) == old_marker:
            print("[--fetch] Die Action hat sich in 3 Minuten nicht gemeldet (GitHub Actions gestoert?). Analysiere, was da ist; spaeter nochmal --fetch.", file=sys.stderr)
        elif "failure" in read(marker):
            print(f"[--fetch] Action gelaufen, aber der Abruf bei chess.com ist fehlgeschlagen ({read(marker).strip()}). Analysiere, was da ist; spaeter nochmal --fetch.", file=sys.stderr)
        elif text == old:
            print(f"[--fetch] Action gelaufen ({read(marker).strip()}). Keine neue Partie. Gerade erst gespielt? chess.com braucht manchmal ein paar Minuten, dann nochmal --fetch.", file=sys.stderr)
        else:
            print(f"[--fetch] Action gelaufen ({read(marker).strip()}). Neue Partien angekommen.", file=sys.stderr)
    elif sys.argv[1] == "--pull":
        if not INBOX_URL:
            raise SystemExit("INBOX_URL in analyze.py ist leer.")
        import urllib.request
        os.makedirs(os.path.join(BASE, "inbox"), exist_ok=True)
        path = os.path.join(BASE, "inbox", "alle.pgn")
        with urllib.request.urlopen(INBOX_URL + ("&" if "?" in INBOX_URL else "?") + f"t={int(datetime.datetime.now().timestamp())}", timeout=60) as r:
            text = r.read().decode("utf-8", errors="replace")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"[--pull] {len(text)} Zeichen nach inbox/alle.pgn", file=sys.stderr)
    else:
        with open(sys.argv[1], encoding="utf-8", errors="replace") as f:
            text = f.read()
    os.makedirs(GAMES_DIR, exist_ok=True)
    chunks = split_pgn(text)
    known = {g["id"] for g in load_progress()["games"]}
    force = "--force" in sys.argv
    for k, pgn_text in enumerate(chunks, 1):
        game_id = hashlib.sha1(re.sub(r"\s+", " ", pgn_text).strip().encode()).hexdigest()[:10]
        if game_id in known and not force:
            print(f"[{k}/{len(chunks)}] schon analysiert ({game_id}), uebersprungen (--force erzwingt)")
            continue
        if len(chunks) > 1:
            print(f"[{k}/{len(chunks)}] analysiere ...", file=sys.stderr)
        try:
            analyze_one(pgn_text, game_id)
        except SystemExit as e:
            print(f"[{k}/{len(chunks)}] uebersprungen: {e}")


def split_pgn(text):
    """Teilt eine Datei in Partien: eine neue beginnt bei einer Header-Zeile, wenn davor Zugtext stand."""
    chunks, cur, in_moves = [], [], False
    for line in text.splitlines():
        if line.startswith("[") and in_moves:
            chunks.append("\n".join(cur).strip()); cur, in_moves = [], False
        elif line.strip() and not line.startswith("["):
            in_moves = True
        cur.append(line)
    if cur:
        chunks.append("\n".join(cur).strip())
    return [c for c in chunks if c]


def analyze_one(pgn_text, game_id):
    r = analyze_game(pgn_text)
    r["id"] = game_id
    opp = r["white"] if r["user_color"] == "Schwarz" else r["black"]
    stem = f"{r['date'].replace('.', '-')}_{opp}_{game_id}"
    with open(os.path.join(GAMES_DIR, stem + ".pgn"), "w") as f:
        f.write(pgn_text)
    with open(os.path.join(GAMES_DIR, stem + ".json"), "w") as f:
        json.dump(r, f, indent=1, ensure_ascii=False)
    txt = text_report(r)
    with open(os.path.join(GAMES_DIR, stem + ".txt"), "w") as f:
        f.write(txt)
    record_progress(r, game_id)
    print(txt)
    try:
        import show
        pngs = show.render_report(os.path.join(GAMES_DIR, stem + ".json"))
        print("\n[Brettbilder: " + ", ".join(os.path.basename(x) for x in pngs) + "]")
    except Exception as e:
        print(f"\n[Brettbilder konnten nicht erzeugt werden: {e}]")
    print(f"[gespeichert: games/{stem}.txt/.json/.pgn | progress.json aktualisiert]")


if __name__ == "__main__":
    main()
