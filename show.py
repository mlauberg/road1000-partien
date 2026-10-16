#!/usr/bin/env python3
"""
Brettbilder. Alles, was Q sieht, kommt hier raus.

Python API:
    from show import storyboard, render
    storyboard("datei.png", title="...", perspective="black", frames=[
        {"moves": "e4 e5 Qh5", "text": "Weiss: Dame raus. Sie zielt auf f7.", "arrows": [("h5","f7","red")]},
        {"fen": "<FEN>", "moves": "Qc6 Nxe7+", "text": "...", "arrows": []},
    ])
    render(fen, "out.png", orientation, played="Qc6", best="Qd7", lastmove="f3f5", caption_lines=[...])

Kommandozeile:
    python3 show.py <report.json>                      -> K Bilder (Lektionskandidaten) und V Bilder (verpasste Chancen)
    python3 show.py fen "<FEN>" out.png [--black] [--played=Qc6] [--best=Qd7]

Farben: gelb = letzter Zug, rot = Drohung oder Fehler, gruen = richtiger Zug, blau = Idee oder Deckung.

KONTROLLE (gilt fuer jeden Pfeil, ohne Ausnahme):
  Jeder Pfeil wird gegen das Brett geprueft: auf dem Startfeld steht eine Figur, das Zielfeld ist ein echter Zug
  oder ein echter Angriff dieser Figur. Sonst ArrowError, kein Bild. Plan Pfeile (Figur steht noch nicht da)
  heissen ("a1", "h8", "blue", "idea") und werden nicht geprueft, der Text muss sie als Plan benennen.
  Zu jedem Frame druckt storyboard() FAKT Zeilen: fuer jedes Pfeilziel und die zuletzt gezogene Figur, wer sie
  angreift und wer sie deckt. Der Bildtext darf ueber gedeckt, ungedeckt, haengt, greift an NUR sagen, was in
  diesen FAKT Zeilen steht.
"""
import sys, os, io, json
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import chess, chess.svg  # noqa: E402
import cairosvg  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

COL = {"red": "#d62828", "green": "#2a9d2a", "blue": "#2b6cb0", "yellow": "#e0a800"}
CHESSCOM = {"square light": "#eeeed2", "square dark": "#769656",
            "square light lastmove": "#f6f669", "square dark lastmove": "#baca2b",
            "margin": "#262522", "coord": "#e6e6e6", "inner border": "#262522", "outer border": "#262522"}
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
PIECE_DE = {chess.PAWN: "Bauer", chess.KNIGHT: "Springer", chess.BISHOP: "Laeufer", chess.ROOK: "Turm", chess.QUEEN: "Dame", chess.KING: "Koenig"}


class ArrowError(Exception):
    pass


def board_after(moves, fen=None):
    b = chess.Board(fen) if fen else chess.Board()
    last = None
    for s in (moves or "").split():
        last = b.parse_san(s); b.push(last)
    return b, last


def validate_arrows(board, arrows):
    for a in arrows:
        f, t, c = a[0], a[1], a[2]
        if len(a) > 3 and a[3] == "idea":
            continue
        fs, ts = chess.parse_square(f), chess.parse_square(t)
        if fs == ts:
            continue  # Feldmarkierung
        p = board.piece_at(fs)
        if p is None:
            raise ArrowError(f"Pfeil {f}->{t}: auf {f} steht keine Figur")
        if c == "green" and p.color != board.turn:
            raise ArrowError(f"Pfeil {f}->{t} ist gruen, aber die Figur auf {f} gehoert nicht der Seite am Zug")
        if ts in board.attacks(fs):
            continue
        b2 = board.copy(); b2.turn = p.color
        if any(m.from_square == fs and m.to_square == ts for m in b2.pseudo_legal_moves):
            continue
        raise ArrowError(f"Pfeil {f}->{t}: {p.symbol()} auf {f} erreicht {t} nicht (weder Zug noch Angriff)")


def piece_name(board, sq):
    p = board.piece_at(sq)
    return f"{'weisser' if p.color else 'schwarzer'} {PIECE_DE[p.piece_type]} {chess.square_name(sq)}" if p else f"leeres Feld {chess.square_name(sq)}"


def square_facts(board, sq):
    """Wer greift das Feld an, wer deckt es, was greift die Figur darauf an. Reiner Brettfakt."""
    p = board.piece_at(sq)
    if p is None:
        w = [chess.square_name(s) for s in board.attackers(chess.WHITE, sq)]
        b = [chess.square_name(s) for s in board.attackers(chess.BLACK, sq)]
        return f"FAKT {chess.square_name(sq)} leer: Weiss sieht es von {', '.join(w) or 'nirgends'}; Schwarz von {', '.join(b) or 'nirgends'}."
    att = [piece_name(board, s) for s in board.attackers(not p.color, sq)]
    dfd = [piece_name(board, s) for s in board.attackers(p.color, sq)]
    hits = []
    for t in board.attacks(sq):
        v = board.piece_at(t)
        if v is not None and v.color != p.color:
            hits.append(f"{PIECE_DE[v.piece_type]} {chess.square_name(t)}" + ("" if board.attackers(v.color, t) else " (ungedeckt)"))
    return (f"FAKT {piece_name(board, sq)}: angegriffen von {', '.join(att) or 'niemandem'}; gedeckt von {', '.join(dfd) or 'niemandem'}; "
            f"greift an: {', '.join(hits) or 'nichts'}.")


def frame_facts(board, arrows, lastmove):
    squares = []
    if lastmove is not None:
        squares.append(lastmove.to_square)
    for a in arrows:
        for s in (chess.parse_square(a[0]), chess.parse_square(a[1])):
            if s not in squares:
                squares.append(s)
    return [square_facts(board, s) for s in squares]


def frame_image(board, orientation, arrows=(), lastmove=None, size=460):
    validate_arrows(board, arrows)
    arr = [chess.svg.Arrow(chess.parse_square(a[0]), chess.parse_square(a[1]), color=COL.get(a[2], a[2])) for a in arrows]
    svg = chess.svg.board(board, orientation=orientation, size=size, arrows=arr, lastmove=lastmove, coordinates=True, colors=CHESSCOM)
    png = cairosvg.svg2png(bytestring=svg.encode(), output_width=size)
    return Image.open(io.BytesIO(png)).convert("RGB")


def wrap(draw, text, font, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= width:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines


def storyboard(out_png, frames, title="", perspective="white", cols=1, size=560, quiet=False):
    orient = chess.WHITE if perspective == "white" else chess.BLACK
    imgs = []
    for k, fr in enumerate(frames, 1):
        b, last = board_after(fr.get("moves", ""), fr.get("fen"))
        if fr.get("lastmove") is not None and last is None:
            last = fr["lastmove"]
        if fr.get("no_last"):
            last = None
        arrows = fr.get("arrows", ())
        imgs.append((frame_image(b, orient, arrows, last, size), fr.get("text", "")))
        if not quiet:
            print(f"[{os.path.basename(out_png)} Frame {k}] " + " | ".join(frame_facts(b, arrows, last)))
    n = len(imgs); cols = min(cols, n); rows = (n + cols - 1) // cols
    f_t, f_c, f_n = ImageFont.truetype(FONT_B, 24), ImageFont.truetype(FONT, 21), ImageFont.truetype(FONT_B, 21)
    cap_h, pad, title_h = 135, 16, (80 if title else 0)
    W = cols * size + (cols + 1) * pad
    H = title_h + rows * (size + cap_h) + (rows + 1) * pad
    canvas = Image.new("RGB", (W, H), "#1e1e1e")
    d = ImageDraw.Draw(canvas)
    if title:
        ty = pad
        for line in wrap(d, title, f_t, W - 2 * pad)[:2]:
            d.text((pad, ty), line, font=f_t, fill="#ffffff"); ty += 30
    for i, (im, text) in enumerate(imgs):
        r, c = divmod(i, cols)
        x, y = pad + c * (size + pad), title_h + pad + r * (size + cap_h + pad)
        canvas.paste(im, (x, y))
        d.text((x, y + size + 8), f"{i + 1}", font=f_n, fill="#f6f669")
        ty = y + size + 8
        for line in wrap(d, text, f_c, size - 34)[:5]:
            d.text((x + 30, ty), line, font=f_c, fill="#f2f2f2"); ty += 25
    canvas.save(out_png)
    return out_png


def render(fen, out_png, orientation=chess.WHITE, played=None, best=None, lastmove=None, caption_lines=None, size=640):
    """Einzelbrett: rot = gespielt, gruen = besser, gelb = letzter Zug."""
    board = chess.Board(fen)
    arrows = []
    if best:
        m = board.parse_san(best) if not isinstance(best, chess.Move) else best
        arrows.append(chess.svg.Arrow(m.from_square, m.to_square, color=COL["green"]))
    if played:
        m = board.parse_san(played) if not isinstance(played, chess.Move) else played
        arrows.append(chess.svg.Arrow(m.from_square, m.to_square, color=COL["red"]))
    lm = None
    if lastmove:
        lm = lastmove if isinstance(lastmove, chess.Move) else chess.Move.from_uci(lastmove)
    svg = chess.svg.board(board, orientation=orientation, size=size, arrows=arrows, lastmove=lm, coordinates=True, colors=CHESSCOM)
    img = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), output_width=size))).convert("RGB")
    if caption_lines:
        pad = 14
        f, fb = ImageFont.truetype(FONT, 20), ImageFont.truetype(FONT_B, 22)
        d0 = ImageDraw.Draw(img)
        rows = []  # (Text, fett) nach Umbruch auf Bildbreite
        for i, line in enumerate(caption_lines):
            for w in wrap(d0, line, fb if i == 0 else f, img.width - 2 * pad):
                rows.append((w, i == 0))
        h = pad * 2 + sum(30 if bold else 28 for _, bold in rows)
        canvas = Image.new("RGB", (img.width, img.height + h), "#1e1e1e")
        canvas.paste(img, (0, 0))
        d = ImageDraw.Draw(canvas)
        y = img.height + pad
        for text, bold in rows:
            d.text((pad, y), text, font=fb if bold else f, fill="#f2f2f2"); y += 30 if bold else 28
        canvas.save(out_png)
    else:
        img.save(out_png)
    return out_png


WORDS = {chess.PAWN: "Bauer", chess.KNIGHT: "Springer", chess.BISHOP: "Läufer", chess.ROOK: "Turm", chess.QUEEN: "Dame", chess.KING: "König"}


def move_words(board, move):
    """Zug in Alltagssprache: 'Dame schlägt e6', 'Springer nach f3 mit Schach', 'kurze Rochade', 'Bauer nach e8, wird Dame'."""
    if isinstance(move, str):
        move = board.parse_san(move)
    if board.is_castling(move):
        s = "kurze Rochade" if chess.square_file(move.to_square) == 6 else "lange Rochade"
    else:
        p = board.piece_at(move.from_square)
        s = f"{WORDS[p.piece_type]} {'schlägt' if board.is_capture(move) else 'nach'} {chess.square_name(move.to_square)}"
        if move.promotion:
            s += f", wird {WORDS[move.promotion]}"
    b2 = board.copy(); b2.push(move)
    if b2.is_checkmate():
        s += ", Matt"
    elif b2.is_check():
        s += " mit Schach"
    return s


def umlaut(text):
    return text.replace("Laeufer", "Läufer").replace("Koenig", "König")


def line_words(board, san_line, n=3, first="du"):
    """Engine Variante ('13...Bxa3 14. Nxa3 Qxe6') als Worte, abwechselnd first ('du' oder 'er') und die andere Seite."""
    b = board.copy(); out = []
    toks = [t for t in san_line.replace("...", " ").split() if not t[0].isdigit()]
    other = "er" if first == "du" else "du"
    for k, t in enumerate(toks[:n]):
        try:
            mv = b.parse_san(t)
        except ValueError:
            break
        out.append((first if k % 2 == 0 else other) + ": " + move_words(b, mv)); b.push(mv)
    return ", ".join(out)


def lesson_storyboard(report, m, out_png, nr):
    """Lektion aus einem kritischen Zug, Text nur aus Report Fakten (Engine, statische Pruefung)."""
    orient = chess.WHITE if report["user_color"] == "Weiss" else chess.BLACK
    b0 = chess.Board(m["fen_before"])
    played, best = b0.parse_san(m["san"]), b0.parse_san(m["best"])
    lm = lastmove_before(report, m["ply"])
    f = m.get("stufe1", {})
    fakt = ""
    if f.get("haengt_neu") or f.get("haengt_nicht_gerettet"):
        fakt = " Danach hängt: " + umlaut(", ".join(x.split(" (")[0] for x in f.get("haengt_neu", []) + f.get("haengt_nicht_gerettet", []))) + "."
    elif f.get("gratis_liegen_gelassen"):
        fakt = " Stand gratis: " + umlaut(", ".join(f.get("gratis_vorher", []))) + "."
    secs = f" (in {m['secs']:.0f} Sekunden gespielt)" if m.get("secs") is not None else ""
    frames = [{"fen": m["fen_before"], "arrows": [(chess.square_name(played.from_square), chess.square_name(played.to_square), "red"),
                                                  (chess.square_name(best.from_square), chess.square_name(best.to_square), "green")],
               "text": f"Zug {m['move_no'].rstrip('.')}: du spieltest {move_words(b0, played)} (rot){secs}. Besser: {move_words(b0, best)} (grün). "
                       f"Gewinnchance {m['win_before']:.0f} % auf {m['win_after']:.0f} %.{fakt}"}]
    # Frame 2: seine beste Antwort auf den gespielten Zug
    b1 = b0.copy(); b1.push(played)
    toks = [t for t in m.get("punish_line", "").replace("...", " ").split() if not t[0].isdigit()]
    if toks:
        try:
            reply = b1.parse_san(toks[0])
            txt = f"Seine beste Antwort: {move_words(b1, reply)} (rot)."
            if "opp_reply_actual" in m:
                txt += " So kam es auch." if m["opp_punished"] else f" Er spielte stattdessen {move_words(b1, m['opp_reply_actual'])}, Glück gehabt."
            frames.append({"fen": b1.fen(), "lastmove": played, "arrows": [(chess.square_name(reply.from_square), chess.square_name(reply.to_square), "red")], "text": txt})
        except ValueError:
            pass
    # Frame 3: nach dem besseren Zug
    b2 = b0.copy(); b2.push(best)
    rest = line_words(b2, " ".join(m.get("best_line", "").split()[1:]), 2, first="er") if m.get("best_line") else ""
    wb = f"deine Gewinnchance {m['win_best']:.0f} %" if "win_best" in m else f"Engine {m.get('eval_best', '?')}"
    frames.append({"fen": b2.fen(), "lastmove": best, "arrows": [],
                   "text": f"Nach {move_words(b0, best)}: {wb}." + (f" Es geht weiter mit {rest}." if rest else "")})
    if lm is not None:
        frames[0]["lastmove"] = lm  # gelb = sein letzter Zug
    title = f"Lektion {nr}: {umlaut(m['drill_grund']) or 'Stellung verstehen'} (Zug {m['move_no'].rstrip('.')}, {m['class']})" + (" WIEDERHOLUNG" if m.get("wiederholung") else "")
    return storyboard(out_png, frames, title=title, perspective="white" if orient == chess.WHITE else "black", quiet=True)


def find_image(report, fnd, out_png, label):
    orient = chess.WHITE if report["user_color"] == "Weiss" else chess.BLACK
    b = chess.Board(fnd["fen"])
    cap = [f"{label}, Zug {fnd['move_no'].rstrip('.')}: {move_words(b, fnd['san'])} (grün)",
           f"Zweitbester wäre {move_words(b, fnd['second'])} gewesen, {fnd['gap']:.0f} Punkte Gewinnchance schlechter."]
    return render(fnd["fen"], out_png, orient, best=fnd["san"], caption_lines=cap)


def lastmove_before(report, ply):
    prev = [x for x in report["moves"] if x["ply"] == ply - 1]
    if not prev:
        return None
    return chess.Board(prev[0]["fen_before"]).parse_san(prev[0]["san"])


def render_report(report_path, max_missed=1):
    """Bilder je Partie: L1, L2 = Lektionen (automatisch gewaehlt), F1, F2 = Funde, V1 = verpasste Chance."""
    with open(report_path) as f:
        r = json.load(f)
    orient = chess.WHITE if r["user_color"] == "Weiss" else chess.BLACK
    stem, outs, seen = report_path[:-5], [], set()
    for k, m in enumerate(r.get("lessons", [])[:2], 1):
        outs.append(lesson_storyboard(r, m, f"{stem}_L{k}.png", k)); seen.add(m["fen_before"])
    for k, (key, label) in enumerate((("best_find", "Bester Fund"), ("hard_find", "Schwierigster Fund")), 1):
        if r.get(key):
            outs.append(find_image(r, r[key], f"{stem}_F{k}.png", label))
    n = 0
    for mc in r.get("missed_chances", []):
        if mc["fen"] in seen or n >= max_missed:
            continue
        n += 1
        b = chess.Board(mc["fen"]); you = mc["you_played"].split()[-1]
        cap = [f"Verpasste Chance nach {mc['after_opp_move']}: du spieltest {move_words(b, you)} (rot)",
               f"Besser: {move_words(b, mc['best'])} (grün). Gewinnchance {mc['win_before']:.0f} % statt {mc['win_after']:.0f} %."]
        outs.append(render(mc["fen"], f"{stem}_V{n}.png", orient, played=you, best=mc["best"], caption_lines=cap))
    return outs


if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "fen":
        fen, out = sys.argv[2], sys.argv[3]
        orient = chess.BLACK if "--black" in sys.argv else chess.WHITE
        played = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--played=")), None)
        best = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--best=")), None)
        print(render(fen, out, orient, played=played, best=best))
    elif len(sys.argv) >= 2 and sys.argv[1].endswith(".json"):
        for p in render_report(sys.argv[1]):
            print(p)
    else:
        print(__doc__)
