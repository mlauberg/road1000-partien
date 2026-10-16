# Road to 1000, Neustart in einem neuen Chat (Stand 16.10.2026, 23:30)

Q schreibt "Road to 1000" oder "Analyse". Kein Zip, kein Anhang. Claude macht in dieser Reihenfolge:

1. Projekt holen (oeffentliches Repo, nur lesen): `git clone https://github.com/mlauberg/road1000-partien.git /home/claude/chess_coach && cd /home/claude/chess_coach`
2. Stockfish 17.1 holen (80 MB, nie im Repo):
   `curl -sSL -o sf.tar https://github.com/official-stockfish/Stockfish/releases/download/sf_17.1/stockfish-ubuntu-x86-64-avx2.tar`
   entpacken, die Datei `stockfish-ubuntu-x86-64-avx2` nach `engine/stockfish` legen, `chmod +x engine/stockfish`.
   Test: `printf "uci\nquit\n" | engine/stockfish | head -1`
3. `pip install --break-system-packages cairosvg`. Die chess Bibliothek liegt als Ordner `chess/` bei (pip chess scheitert in der Umgebung).
4. `COACH_PROTOCOL.md`, `LEHRPLAN.md` und `KONZEPTE.md` komplett lesen. Drei kurze Texte: Regeln, Lernmethode, Theoriekarten.
5. Stand laden (Fortschritt und Drills leben in der Datenbank des Artefakts "Road to 1000", Adresse unten): mit dem Werkzeug ArtifactData
   `list` fuer die Sammlungen `partien`, `drills` und `drill_log` (jeweils `query: {"limit": 1000}`, `out_dir: /home/claude/chess_coach/sync_in`)
   und `get` fuer `meta/stand` (gleicher out_dir). Dann `python3 sync.py import sync_in`. Ergebnis: progress.json und drills.json.
6. Neue Partien: `python3 analyze.py --pull` (holt `inbox/alle.pgn` vom Repo, das der Oracle Server alle 2 Minuten fuellt, analysiert alles Neue). Je neuer Partie `python3 drill.py add games/<report>.json`. Notweg, falls der Server haengt: Q haengt eine PGN an, `python3 analyze.py <datei>`.
7. Tageseinheit nach Lehrplan: Drills (`drill.py quiz`, `reveal`), Lektionsbilder L1, L2, F1, F2 je Partie, Trend (`analyze.py --progress`).
8. Stand sichern, am Ende und nach jedem Drill Block: `python3 sync.py export sync_out`, dann die gedruckten Eintraege mit ArtifactData `batch` schreiben (max 50 je Aufruf; es sind nur neue Dokumente, kein if_version noetig). Meldet export einen Stufenwechsel: `meta/stand` mit `get` lesen und mit `set` plus `if_version` setzen. Danach zeigt die Seite "Road to 1000" den neuen Stand.

Artefakt (Datenbank und Seite mit Rating, Kennzahlen, Drill Pool): https://claude.ai/artifact/E46EePzEV7k5vKzM8i5Bhb

Repertoire und Fallen Bilder (`python3 bilder.py`, 30 Sekunden) nur bauen, wenn Q eines sehen will.

## Werkzeuge (sieben Dateien, dazu vier Texte: Protokoll, Lehrplan, Konzepte, dieser Neustart)
* `analyze.py <pgn> | --pull | --fetch | --progress`: Stockfish Analyse mit 2 Engines parallel, waehlt Lektion 1 und 2 (erst aktuelle Stufe, dann Wiederholung, dann groesster Verlust), rendert L1, L2 (Lektionen, 3 Bilder, Text nur aus Engine Fakten, in Worten), F1, F2 (Funde), V1 (verpasste Chance), fuehrt progress.json. `--progress`: Trend, Kennzahlen, Stufenfreigabe, faellige Konzepte. STUFE steht oben in analyze.py.
* `drill.py add | quiz | reveal | stats | prune | speed`: Drill Pool zur aktuellen Stufe, Wiederholung nach 3 und 7 Tagen, Loesungen in Worten, woechentliche Schnellrunde.
* `sync.py import | export`: Stand aus der Artefakt Datenbank laden und neue Dokumente dorthin vorbereiten (nur Anlegen, nie Aendern).
* `show.py`: Bilderfolgen (storyboard) und Einzelbretter (render), Zuege in Worten (move_words). Pfeilpruefung, FAKT Zeilen je Frame.
* `check.py line | fen | move | hang`: Faktencheck fuer alles, was Claude frei ueber eine Stellung sagen will.
* `bilder.py`: Repertoire A bis F, Fallen 01 bis 06, Lektion Laeufer eingesperrt. Reproduzierbar, auf Abruf.
* `fetch_chesscom.py`: laeuft NICHT hier, sondern auf dem Oracle Server (Benutzer road1000, eigene Fassung dort, Timer alle 2 Minuten, pusht `inbox/` ins Repo).

## Warum so
Aus der Claude Umgebung ist nur GitHub und Paketquellen erreichbar (geprueft 16.10.2026: example.com, oracle.com, ntfy.sh, api.chess.com alle 403; raw.githubusercontent.com, git clone, Python urllib gehen). Schreiben nach GitHub ginge nur ueber einen GitHub Connector mit Qs privatem Konto; verbunden ist aber das Gore Konto, und das bleibt da raus. Deshalb: Code und Partien kommen aus dem Repo (lesen), der Fortschritt liegt in der Artefakt Datenbank (lesen und schreiben, ohne Connector). Reports in `games/` sind Sitzungsware und werden nicht gesichert; alles, was spaeter gebraucht wird (Kennzahlen, Lektionsmuster, Stellungen fuer Konzeptlektionen), steht in progress.json.

## Falls Qs privates GitHub doch mal in claude.ai verbunden ist
Dann kann Claude ins Repo schreiben: `python3 analyze.py --fetch` stoesst den Abruf per Push auf request.txt sofort an (GitHub Action aus `.github/workflows/fetch.yml` im Backup Zip, Secret CONTACT im Repo), und der Oracle Timer kann aus. Vorher pruefen: "liste meine GitHub Repos" muss `road1000-partien` mit Schreibrecht zeigen.

## Stand 16.10.2026, 23:30
* Rating nach Partie 7: 612 (Start 480 am 14.10.). 7 Partien, alle Rapid 10+0, mit Uhr.
* Stufe 1 (Captures). Letzte 7: haengen gelassen 0,86 je Partie, gratis genommen 89 %, Gegnerpatzer genutzt 45 %, Koenig in 4 von 7 nach Zug 12 in der Mitte, Blunder unter 5 Sekunden 5 von 26. Konzept faellig: Figur haengen lassen, nicht gerettet, Koenigssicherheit (eine pro Woche).
* Drill Pool: 10 Aufgaben, 4 Antworten bisher (alle richtig), Faelligkeiten werden aus dem Antwortlog berechnet.
* Datenbank: 7 Partien, 10 Drills, 4 Antworten, meta/stand (stufe 1).
