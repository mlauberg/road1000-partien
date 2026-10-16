#!/usr/bin/env python3
"""Alle festen Bilderfolgen (Repertoire, Fallen, eine Lektion). Neu bauen: python3 bilder.py
Jeder Pfeil wird geprueft, jeder Frame druckt FAKT Zeilen. Bricht ein Bild ab, wird die Definition hier korrigiert.
Linien am 14.10.2026 mit Stockfish Tiefe 20 geprueft (check.py line "...")."""
import os, sys
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
from show import storyboard, ArrowError  # noqa: E402
for d in ("repertoire", "fallen", "lektionen"):
    os.makedirs(os.path.join(BASE, d), exist_ok=True)
jobs = []

# ---------------- Repertoire ----------------
jobs.append(("repertoire/A_weiss_italienisch.png", dict(title="Als Weiß: immer 1.e4 und Italienisch. Dein fester Aufbau.", perspective="white", frames=[
 {"moves": "e4", "text": "Zug 1: immer Bauer e4. Zentrum, Läufer und Dame werden frei.", "arrows": []},
 {"moves": "e4 e5 Nf3", "text": "Springer f3 greift e5 an (blau). Zug 2, immer.", "arrows": [("f3", "e5", "blue")]},
 {"moves": "e4 e5 Nf3 Nc6 Bc4", "text": "Läufer c4 zielt auf f7 (blau), den schwächsten Punkt beim Gegner. Das ist Italienisch. Zug 3, immer.", "arrows": [("c4", "f7", "blue")]},
 {"moves": "e4 e5 Nf3 Nc6 Bc4 Bc5 c3 Nf6 d3 d6 O-O O-O", "text": "Antwortet er mit Läufer c5: Bauer c3, Bauer d3, Rochade. Deine Grundstellung. Danach Springer b1 nach d2, Turm nach e1, Bauer b4 (blau).", "arrows": [("b1", "d2", "blue"), ("f1", "e1", "blue"), ("b2", "b4", "blue")]},
 {"moves": "e4 e5 Nf3 Nc6 Bc4 Nf6", "text": "Antwortet er mit Springer f6: Springer g5 (grün). Das Angriffsbild von vorhin, Free Elo.", "arrows": [("f3", "g5", "green")]},
 {"moves": "e4 d5 exd5 Qxd5 Nc3", "text": "Spielt er Skandinavisch gegen dich: nehmen, dann Springer c3 greift die Dame an (blau). Danach Bauer d4, Springer f3, Läufer d2.", "arrows": [("c3", "d5", "blue")]},
 {"moves": "e4 c5 Nf3 Nc6 Bc4", "text": "Gegen alles andere (c5, e6, c6): Springer f3, Läufer c4 oder d3, Rochade, dann Bauer d4. Erst alle Figuren raus, dann angreifen.", "arrows": []},
])))
jobs.append(("repertoire/B_schwarz_gegen_e4_skandinavisch.png", dict(title="Als Schwarz gegen e4: Skandinavisch. Dein fester Aufbau.", perspective="black", frames=[
 {"moves": "e4 d5", "text": "Bauer d5 greift e4 an. Zug 1, immer.", "arrows": [("d5", "e4", "blue")]},
 {"moves": "e4 d5 exd5 Qxd5", "text": "Er nimmt, du nimmst mit der Dame zurück.", "arrows": []},
 {"moves": "e4 d5 exd5 Qxd5 Nc3 Qa5", "text": "Springer c3 greift die Dame an: Dame nach a5. Immer dieser Zug.", "arrows": []},
 {"moves": "e4 d5 exd5 Qxd5 Nc3 Qa5 d4 Nf6 Nf3 Bg4", "text": "Dann Springer f6 und Läufer g4. Der Läufer greift den Springer f3 an (blau), dahinter steht seine Dame: Fesselung.", "arrows": [("g4", "f3", "blue"), ("g4", "d1", "blue", "idea")]},
 {"moves": "e4 d5 exd5 Qxd5 Nc3 Qa5 d4 Nf6 Nf3 Bg4 Be2 e6 O-O c6", "text": "Dann Bauer e6 und Bauer c6. WICHTIG: c6 früh, es gibt der Dame den Rückweg nach c7 (blau) und stoppt Springer nach b5 oder d5. Danach Läufer e7, Rochade.", "arrows": [("a5", "c7", "blue"), ("f8", "e7", "blue")]},
 {"moves": "e4 d5 Nc3 dxe4 Nxe4 Nf6", "text": "Nimmt er nicht und spielt Springer c3: du schlägst e4, er schlägt zurück, Springer f6. Ausgeglichen.", "arrows": []},
 {"moves": "e4 d5 e5 Bf5 d4 e6 Nf3 c5", "text": "Schiebt er den Bauern nach e5: Läufer f5 raus, Bauer e6, Bauer c5 greift sein Zentrum an. Angenehm für dich.", "arrows": [("c5", "d4", "blue")]},
])))
jobs.append(("repertoire/C_schwarz_gegen_d4.png", dict(title="Als Schwarz gegen d4: Bauer d5 und e6. Dein fester Aufbau.", perspective="black", frames=[
 {"moves": "d4 d5", "text": "Bauer d5. Zug 1, immer.", "arrows": []},
 {"moves": "d4 d5 c4 e6", "text": "Bietet er den Bauern c4 an: NICHT nehmen. Bauer e6 deckt d5 (blau).", "arrows": [("e6", "d5", "blue")]},
 {"moves": "d4 d5 c4 e6 Nc3 Nf6 Bg5 Be7", "text": "Springer f6, Läufer e7. Der Läufer deckt den Springer, die Fesselung ist harmlos.", "arrows": [("e7", "f6", "blue")]},
 {"moves": "d4 d5 c4 e6 Nc3 Nf6 Bg5 Be7 e3 O-O Nf3 Nbd7", "text": "Rochade, Springer b8 nach d7. Fertig. Danach Bauer c5 und Bauer b6 mit Läufer b7 (blau).", "arrows": [("c7", "c5", "blue"), ("b7", "b6", "blue")]},
 {"moves": "d4 d5 Bf4 Nf6 e3 c5 c3 Nc6 Nd2 e6 Ngf3 Bd6", "text": "Spielt er früh Läufer f4 (Londoner System): Springer f6, Bauer c5, Springer c6, Bauer e6, Läufer d6 bietet den Tausch an. Ausgeglichen.", "arrows": [("d6", "f4", "blue")]},
 {"moves": "d4 d5 Nf3 Nf6 c4 e6", "text": "Reihenfolge egal: immer d5, Springer f6, e6, Läufer e7, Rochade. Diese Züge gehen gegen fast alles, was er mit d4 macht.", "arrows": []},
])))
jobs.append(("repertoire/D_schwarz_entscheidung.png", dict(title="Als Schwarz: Zug 1 vom Gegner anschauen, dann gibt es nur zwei Fälle", perspective="black", frames=[
 {"moves": "e4", "text": "Fall 1: Gegner spielt Bauer e4 (gelb). Du: Bauer d5. Das ist Skandinavisch, Bild B. Dame nimmt zurück, Dame nach a5, dann Springer f6, Läufer g4, c6, e6.", "arrows": [("d7", "d5", "green")]},
 {"moves": "d4", "text": "Fall 2: Gegner spielt Bauer d4 (gelb). Du: Bauer d5. Dann e6, Springer f6, Läufer e7, Rochade. Bild C. Slawisch (c6) brauchst du NICHT, vergiss das Wort.", "arrows": [("d7", "d5", "green")]},
 {"moves": "c4", "text": "Fall 3, selten: Gegner spielt etwas anderes (c4, Springer f3). Auch dann: Bauer d5, dann e6, Springer f6, Läufer e7, Rochade. Immer das gleiche Haus bauen.", "arrows": [("d7", "d5", "green")]},
])))
jobs.append(("repertoire/E_schwarz_zug2.png", dict(title="Als Schwarz, Zug 2: nur zwei Regeln", perspective="black", frames=[
 {"moves": "e4 d5 exd5", "text": "REGEL 1: Schlägt er deinen Bauern d5, nimmst du mit der Dame zurück (grün). Greift danach ein Springer die Dame an: Dame nach a5.", "arrows": [("d8", "d5", "green")]},
 {"moves": "c4 d5 cxd5", "text": "Regel 1 gilt auch, wenn er mit dem c Bauern schlägt (nach 1.c4): Dame nimmt zurück, später Dame a5. Dieselbe Stellung wie im Skandinavisch.", "arrows": [("d8", "d5", "green")]},
 {"moves": "d4 d5 c4", "text": "REGEL 2: Schlägt er nicht, kommt dein Springer nach f6 (grün). Einzige Ausnahme: bietet er den Bauern c4 an, erst Bauer e6 (blau), Springer f6 im Zug danach.", "arrows": [("e7", "e6", "blue"), ("g8", "f6", "green")]},
 {"moves": "d4 d5 Nf3", "text": "Regel 2: Springer f6. Gilt gegen Springer f3, Läufer f4, Springer c3, Bauer e3, alles. Danach e6, Läufer e7, Rochade.", "arrows": [("g8", "f6", "green")]},
 {"moves": "e4 d5 Nc3", "text": "Sonderfall nach e4: schlägt er nicht, sondern spielt Springer c3, dann schlägst DU den Bauern e4 (grün). Er nimmt zurück, dann Springer f6.", "arrows": [("d5", "e4", "green")]},
 {"moves": "e4 d5 e5", "text": "Sonderfall nach e4: schiebt er den Bauern nach e5, dann Läufer f5 raus (grün), erst danach Bauer e6, dann c5. Deine Regel: Läufer vor Bauer.", "arrows": [("c8", "f5", "green")]},
])))
jobs.append(("repertoire/F_das_haus.png", dict(title="Gegen Zufallszüge: du spielst nicht gegen seine Züge, du baust dein Haus", perspective="white", frames=[
 {"moves": "e4 a6 Nf3 h6 Bc4 b6 Nc3 g6 d3 c6 O-O Bb7 Be3 d6 Qd2", "text": "Dein Haus als Weiß, egal was er macht: Bauer e4, Springer f3, Läufer c4, Springer c3, Bauer d3, Rochade, Läufer e3, Dame d2. Hier hat er 7 Zufallszüge gespielt. Du bist fertig entwickelt, er hat nichts. Engine: besser für dich (+0.8).", "arrows": []},
 {"moves": "e4 e5 Nf3 Nc6 Bc4 Nf6 Nc3 h6 d3 a6 O-O b5", "text": "Vor jedem Zug drei Blicke. Hier: Greift er etwas an? Ja, Bauer b5 greift deinen Läufer an (rot). Also erst Läufer retten (grün nach b3), DANN das Haus weiterbauen. Greift nichts an und hängt nichts bei ihm: nächster Hauszug.", "arrows": [("b5", "c4", "red"), ("c4", "b3", "green")]},
 {"moves": "e4 e5 Nf3 Nc6 Bc4 Nf6 Nc3 Bb4 O-O Bxc3", "text": "Und wenn er dir etwas gibt: nehmen. Hier schlägt er deinen Springer, du nimmst zurück (grün). Zufallszüge sind entweder Drohung (abwehren), Geschenk (nehmen) oder nichts (Haus bauen). Mehr Fälle gibt es nicht.", "arrows": [("b2", "c3", "green")]},
])))

# ---------------- Lektion: Laeufer eingesperrt ----------------
L = "d4 d5 c4 e6 Nc3 Nf6 Bg5 Be7 e3 O-O Nf3 Nbd7 Bd3 b6 O-O Bb7"
jobs.append(("lektionen/laeufer_eingesperrt.png", dict(title="Warum Bauer e6 trotz eingesperrtem Läufer ok ist", perspective="black", frames=[
 {"moves": "d4 d5 c4 e6", "text": "Du hast recht: Bauer e6 sperrt den Läufer c8 ein, er läuft gegen den eigenen Bauern (rot). Das ist der bekannte Nachteil dieses Aufbaus. Dafür ist d5 felsenfest (blau) und der Läufer f8 kommt raus.", "arrows": [("c8", "e6", "red"), ("e6", "d5", "blue"), ("f8", "e7", "blue")]},
 {"moves": "d4 d5 c4 e6 Nc3 Nf6 Bg5 Be7 e3 O-O Nf3 Nbd7 Bd3 b6", "text": "Die Lösung ist fester Teil des Plans: Bauer b6 (gelb), dann Läufer nach b7 (blau). Von dort zielt er auf die lange Diagonale.", "arrows": [("c8", "b7", "blue")]},
 {"moves": L, "text": "Läufer auf b7, alle Figuren entwickelt, König sicher. Engine: ausgeglichen. Noch steht dein Bauer d5 vor ihm (blau). Sobald der weg ist, nach Bauer c5 oder d5 schlägt c4, sieht der Läufer bis e4 und weiter. Eingesperrt ist nur schlimm, wenn es dauerhaft ist.", "arrows": [("b7", "d5", "blue")]},
 {"moves": "e4 d5 exd5 Qxd5 Nc3 Qa5 d4 Nf6 Nf3 Bg4", "text": "Deine Regel in Aktion: im Skandinavisch kommt der Läufer ZUERST nach g4 (gelb), erst danach Bauer e6 (blau). Genau deshalb ist die Zugfolge dort so.", "arrows": [("e7", "e6", "blue")]},
 {"moves": "d4 d5 c4 c6", "text": "Alternative, wenn es dich stört: Bauer c6 statt e6 (Slawisch). Der Läufer bleibt frei und geht nach f5 (blau). Nachteil: Bauer b7 wird dann oft von der Dame auf b3 angegriffen. Für dich: bleib bei e6 plus b6 und Läufer b7.", "arrows": [("c8", "f5", "blue")]},
])))

# ---------------- Fallen ----------------
jobs.append(("fallen/01_schaefermatt_abwehr.png", dict(title="Als Schwarz: Schäfermatt Versuch abwehren (Dame kommt früh)", perspective="black", frames=[
    {"moves": "e4 e5 Qh5", "text": "Weiß zieht die Dame früh raus. Sie zielt auf deinen Bauern f7 und auf e5 (rot). Nicht erschrecken.", "arrows": [("h5", "f7", "red"), ("h5", "e5", "red")]},
    {"moves": "e4 e5 Qh5 Nc6", "text": "Du: Springer nach c6 (gelb). Er deckt e5 (blau). Ganz normaler Entwicklungszug.", "arrows": [("c6", "e5", "blue")]},
    {"moves": "e4 e5 Qh5 Nc6 Bc4", "text": "Weiß: Läufer c4. Jetzt droht Dame schlägt f7 MATT (rot). NIEMALS Springer f6 (rot, verliert sofort). Richtig: Bauer g6 (grün), greift die Dame an.", "arrows": [("h5", "f7", "red"), ("c4", "f7", "red"), ("g8", "f6", "red"), ("g7", "g6", "green")]},
    {"moves": "e4 e5 Qh5 Nc6 Bc4 g6 Qf3", "text": "Die Dame weicht nach f3 aus und droht wieder f7 (rot). Du: Springer f6 (grün), deckt f7 und entwickelt. Drohung erledigt.", "arrows": [("f3", "f7", "red"), ("g8", "f6", "green")]},
    {"moves": "e4 e5 Qh5 Nc6 Bc4 g6 Qf3 Nf6 Qb3", "text": "Weiß versucht es ein drittes Mal: Läufer c4 greift f7 an (rot), die Dame b3 steht als Batterie dahinter. Jetzt Springer d4! (grün). Er greift die Dame an UND den Bauern c2.", "arrows": [("c4", "f7", "red"), ("c6", "d4", "green")]},
    {"moves": "e4 e5 Qh5 Nc6 Bc4 g6 Qf3 Nf6 Qb3 Nd4", "text": "Springer auf d4 bedroht Dame b3 und Bauer c2 (blau). Weiß hat nur Zeit verloren, du hast alles entwickelt. Engine: +3.6 für dich.", "arrows": [("d4", "b3", "blue"), ("d4", "c2", "blue")]},
])))
jobs.append(("fallen/02_giuoco_springer_gratis.png", dict(title="Als Schwarz: Springer g5 zu früh = Springer gratis", perspective="black", frames=[
    {"moves": "e4 e5 Nf3 Nc6 Bc4 Bc5", "text": "Italienisch. Dein Läufer steht auf c5, der Springer auf c6. Alles normal.", "arrows": []},
    {"moves": "e4 e5 Nf3 Nc6 Bc4 Bc5 Ng5", "text": "Weiß springt nach g5 und droht f7 (rot). Aber: der Springer auf g5 ist UNGEDECKT, und deine Dame sieht ihn (grün).", "arrows": [("g5", "f7", "red"), ("c4", "f7", "red"), ("d8", "g5", "green")]},
    {"moves": "e4 e5 Nf3 Nc6 Bc4 Bc5 Ng5 Qxg5", "text": "Dame schlägt g5. Springer gratis, keine Gefahr mehr. Engine: +4 für dich. Das passiert auf deinem Level ständig.", "arrows": []},
])))
jobs.append(("fallen/03_vierspringer_gabeltrick.png", dict(title="Als Schwarz: der Gabeltrick im Vierspringer (und warum du ihn als Weiß nie zulässt)", perspective="black", frames=[
    {"moves": "e4 e5 Nf3 Nc6 Nc3 Nf6 Bc4", "text": "Weiß spielt Läufer c4. Sieht harmlos aus. Dein Springer f6 darf e4 schlagen (grün), obwohl der Springer c3 den Bauern deckt.", "arrows": [("f6", "e4", "green")]},
    {"moves": "e4 e5 Nf3 Nc6 Nc3 Nf6 Bc4 Nxe4 Nxe4", "text": "Weiß schlägt zurück. Jetzt Bauer d5 (grün): GABEL auf Läufer c4 und Springer e4 (blau). Eine Figur holst du dir zurück.", "arrows": [("d7", "d5", "green"), ("d5", "c4", "blue", "idea"), ("d5", "e4", "blue", "idea")]},
    {"moves": "e4 e5 Nf3 Nc6 Nc3 Nf6 Bc4 Nxe4 Nxe4 d5", "text": "Die Gabel steht. Material wird gleich, du hast das Zentrum. Engine: ausgeglichen, bequem für dich.", "arrows": [("d5", "c4", "blue"), ("d5", "e4", "blue")]},
    {"moves": "e4 e5 Nf3 Nc6 Nc3 Nf6 Bc4 Nxe4 Bxf7+ Kxf7 Nxe4 d5", "text": "Opfert Weiß stattdessen auf f7 und schlägt dann e4: wieder Bauer d5 Gabel. Engine +1.6 für dich. Merke als Weiß: im Vierspringer nie Läufer c4.", "arrows": [("d5", "e4", "blue")]},
])))
jobs.append(("fallen/04_italienisch_springer_g5_angriff.png", dict(title="Als Weiß: der Springer g5 Angriff in der Italienischen (so holst du Free Elo)", perspective="white", frames=[
    {"moves": "e4 e5 Nf3 Nc6 Bc4 Nf6", "text": "Gegner spielt Springer f6. Jetzt dein Springer nach g5 (grün): Läufer und Springer zielen beide auf f7 (blau).", "arrows": [("f3", "g5", "green"), ("c4", "f7", "blue")]},
    {"moves": "e4 e5 Nf3 Nc6 Bc4 Nf6 Ng5 h6", "text": "Antwort A: Bauer h6?? will den Springer vertreiben. Du: Springer schlägt f7 (grün) und gabelt Dame und Turm (blau). Engine +4.", "arrows": [("g5", "f7", "green"), ("f7", "d8", "blue", "idea"), ("f7", "h8", "blue", "idea")]},
    {"moves": "e4 e5 Nf3 Nc6 Bc4 Nf6 Ng5 Nxe4", "text": "Antwort B: Springer schlägt e4?? Du: Läufer schlägt f7 mit Schach (grün). Der König muss nach e7, danach Bauer d4. Engine +2.3.", "arrows": [("c4", "f7", "green")]},
    {"moves": "e4 e5 Nf3 Nc6 Bc4 Nf6 Ng5 d5 exd5 Nxd5", "text": "Antwort C: Bauer d5, du schlägst, Springer schlägt zurück. Jetzt Fried Liver: Springer schlägt f7! (grün)", "arrows": [("g5", "f7", "green")]},
    {"moves": "e4 e5 Nf3 Nc6 Bc4 Nf6 Ng5 d5 exd5 Nxd5 Nxf7 Kxf7 Qf3+", "text": "König nimmt, Dame f3 Schach. Der König MUSS nach e6 (blau) und steht mitten im Brett. Dann Springer c3 greift d5 an. Auf 500 Niveau fast immer gewonnen.", "arrows": [("f3", "d5", "red"), ("f7", "e6", "blue")]},
    {"moves": "e4 e5 Nf3 Nc6 Bc4 Nf6 Ng5 d5 exd5 Na5", "text": "Antwort D (die einzig gute): Springer a5 greift deinen Läufer an (rot). Du: Läufer b5 Schach (grün), dann Bauer c6, du schlägst, er schlägt zurück. Material gleich.", "arrows": [("a5", "c4", "red"), ("c4", "b5", "green")]},
])))
jobs.append(("fallen/05_blackburne_falle.png", dict(title="Als Weiß: der Springer d4 Köder (NICHT e5 nehmen)", perspective="white", frames=[
    {"moves": "e4 e5 Nf3 Nc6 Bc4 Nd4", "text": "Gegner stellt den Springer auf d4 und lässt e5 scheinbar hängen. FALLE. Nicht e5 nehmen (rot). Richtig: Springer schlägt d4 (grün).", "arrows": [("f3", "e5", "red"), ("f3", "d4", "green")]},
    {"moves": "e4 e5 Nf3 Nc6 Bc4 Nd4 Nxe5 Qg5", "text": "Wenn du e5 nimmst: Dame g5 greift Springer e5 UND Bauer g2 an (rot). Jetzt bist du schon in Schwierigkeiten.", "arrows": [("g5", "e5", "red"), ("g5", "g2", "red")]},
    {"moves": "e4 e5 Nf3 Nc6 Bc4 Nd4 Nxe5 Qg5 Nxf7 Qxg2 Rf1 Qxe4+ Be2 Nf3#", "text": "Gier auf f7 endet so: Dame frisst g2, dann e4 mit Schach, Springer f3 MATT. Verloren nach 7 Zügen.", "arrows": []},
    {"moves": "e4 e5 Nf3 Nc6 Bc4 Nd4 Nxd4 exd4", "text": "Richtig gespielt: Springer schlägt d4, Bauer schlägt zurück. Du stehst besser (Engine +1.4). Rochieren, fertig.", "arrows": []},
])))
jobs.append(("fallen/06_legal_matt.png", dict(title="Als Weiß: das Legal Matt (Dame opfern, Matt in 2)", perspective="white", frames=[
    {"moves": "e4 e5 Nf3 d6 Bc4 Bg4", "text": "Gegner fesselt deinen Springer f3 mit dem Läufer g4 (rot). Er glaubt, der Springer darf nie ziehen.", "arrows": [("g4", "f3", "red"), ("g4", "d1", "red", "idea")]},
    {"moves": "e4 e5 Nf3 d6 Bc4 Bg4 Nc3 g6", "text": "Du: Springer c3. Spielt der Gegner jetzt einen Zug ohne Sinn wie Bauer g6: Springer schlägt e5! (grün). Ja, die Dame hängt. Egal.", "arrows": [("f3", "e5", "green")]},
    {"moves": "e4 e5 Nf3 d6 Bc4 Bg4 Nc3 g6 Nxe5 Bxd1", "text": "Er nimmt die Dame. Jetzt Läufer schlägt f7 Schach (grün). Der König muss nach e7.", "arrows": [("c4", "f7", "green")]},
    {"moves": "e4 e5 Nf3 d6 Bc4 Bg4 Nc3 g6 Nxe5 Bxd1 Bxf7+ Ke7 Nd5#", "text": "Springer d5: SCHACHMATT. Läufer f7 und Springer e5 nehmen dem König alle Felder. Nimmt er stattdessen e5 mit dem Bauern: du schlägst den Läufer g4, Bauer vorn (+2.1).", "arrows": []},
])))

errors = []
for out, kw in jobs:
    try:
        storyboard(os.path.join(BASE, out), quiet=True, **kw)
        print("OK  ", out)
    except ArrowError as e:
        errors.append((out, str(e))); print("FEHL", out, "->", e)
    except Exception as e:
        errors.append((out, repr(e))); print("CRASH", out, "->", repr(e))
print("Fehler:", len(errors))
sys.exit(1 if errors else 0)
