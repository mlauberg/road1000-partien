#!/usr/bin/env python3
"""
Faktencheck fuer alles, was Claude ueber eine Stellung schreibt. Erst rechnen, dann behaupten.

    python3 check.py line "e4 e5 Nf3 Nc6 Bc4 Nf6 Ng5"        Eval + 3 beste Zuege + Variante nach dieser Zugfolge
    python3 check.py fen "<FEN>"                              dasselbe fuer eine Stellung
    python3 check.py fen "<FEN>" e7 f5                        zusaetzlich: wer greift e7 und f5 an, wer deckt, was greifen sie an
    python3 check.py move "<FEN>" Qd7                         ist dieser Zug gut? Gewinnchance vorher/nachher, Klasse, bester Zug
    python3 check.py hang "<FEN>"                             alle Figuren beider Seiten, die gerade gratis oder mit Verlust schlagbar sind

Tiefe 20, eine Engine. Ausgabe ist der einzige erlaubte Beleg fuer Eval, "gedeckt", "ungedeckt", "haengt", "greift an".
"""
import sys, os
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import chess, chess.engine  # noqa: E402
from analyze import win_prob, classify, fmt_score, en_prise, ENGINE_PATH, PIECE_DE  # noqa: E402
from show import square_facts  # noqa: E402

DEPTH = 20


def engine():
    e = chess.engine.SimpleEngine.popen_uci(ENGINE_PATH)
    e.configure({"Threads": 1, "Hash": 256})
    return e


def top_moves(e, board, n=3):
    if board.is_game_over():
        return "Partie ist zu Ende: " + ("Matt" if board.is_checkmate() else "Remis oder Patt")
    info = e.analyse(board, chess.engine.Limit(depth=DEPTH), multipv=n)
    out = [f"Eval (Weiss Sicht) {fmt_score(info[0]['score'].white())}, Gewinnchance {'Weiss' if board.turn else 'Schwarz'} am Zug {win_prob(info[0]['score'].pov(board.turn)):.0f} %"]
    for k, i in enumerate(info, 1):
        if i.get("pv"):
            out.append(f"  {k}. {board.san(i['pv'][0]):<7} {fmt_score(i['score'].white()):>6}  {board.variation_san(i['pv'][:6])}")
    return "\n".join(out)


def main(a):
    if len(a) < 2:
        print(__doc__); return
    cmd = a[0]
    if cmd == "line":
        b = chess.Board()
        for s in a[1].split():
            b.push_san(s)
    else:
        b = chess.Board(a[1])
    e = engine()
    try:
        if cmd in ("line", "fen"):
            print(top_moves(e, b))
            for sq in a[2:]:
                print(square_facts(b, chess.parse_square(sq)))
        elif cmd == "move":
            mv = b.parse_san(a[2])
            before = e.analyse(b, chess.engine.Limit(depth=DEPTH))
            b2 = b.copy(); b2.push(mv)
            after = e.analyse(b2, chess.engine.Limit(depth=DEPTH)) if not b2.is_game_over() else None
            wb = win_prob(before["score"].pov(b.turn))
            wa = 100.0 if (after is None and b2.is_checkmate()) else (50.0 if after is None else win_prob(after["score"].pov(b.turn)))
            best = b.san(before["pv"][0])
            cls = "BEST" if before["pv"][0] == mv else classify(wb - wa, 0)
            print(f"{a[2]}: Gewinnchance {wb:.0f} % -> {wa:.0f} % ({wb - wa:+.0f}), Klasse {cls}, bester Zug {best}")
            if after is not None and after.get("pv"):
                print(f"  Antwort der Engine auf {a[2]}: {b2.variation_san(after['pv'][:6])}")
        elif cmd == "hang":
            for color, name in ((chess.WHITE, "Weiss"), (chess.BLACK, "Schwarz")):
                ep = en_prise(b, color)
                print(f"{name}: " + (", ".join(f"{PIECE_DE[b.piece_at(s).piece_type]} {chess.square_name(s)} ({how})" for s, how in ep.items()) or "nichts haengt"))
        else:
            print(__doc__)
    finally:
        e.quit()


if __name__ == "__main__":
    main(sys.argv[1:])
