# Road to 1000, Neustart in einem neuen Chat (Stand 17.10.2026, 00:00)

Q schreibt "Road to 1000" oder "Analyse". Kein Zip, kein Anhang. Claude macht in dieser Reihenfolge:

1. Projekt holen: das Repo `mlauberg/road1000-partien` an die Sitzung haengen (im Chat auswaehlen oder add_repo mit Schreibrecht, GitHub Konto mlauberg). Der Klon liegt dann unter `/home/claude/road1000-partien`, dort arbeiten. Ohne Schreibrecht geht nur lesen: `git clone https://github.com/mlauberg/road1000-partien.git` und statt `--fetch` immer `--pull`.
2. Stockfish 17.1 holen (80 MB, nie im Repo):
   `curl -sSL -o sf.tar https://github.com/official-stockfish/Stockfish/releases/download/sf_17.1/stockfish-ubuntu-x86-64-avx2.tar`
   entpacken, die Datei `stockfish-ubuntu-x86-64-avx2` nach `engine/stockfish` legen, `chmod +x engine/stockfish`.
   Test: `printf "uci\nquit\n" | engine/stockfish | head -1`
3. `pip install --break-system-packages cairosvg`. Die chess Bibliothek liegt als Ordner `chess/` bei (pip chess scheitert in der Umgebung).
4. `COACH_PROTOCOL.md`, `LEHRPLAN.md` und `KONZEPTE.md` komplett lesen. Drei kurze Texte: Regeln, Lernmethode, Theoriekarten.
5. Stand laden (Fortschritt und Drills leben in der Datenbank des Artefakts "Road to 1000", Adresse unten): mit dem Werkzeug ArtifactData
   `list` fuer die Sammlungen `partien`, `drills` und `drill_log` (jeweils `query: {"limit": 1000}`, `out_dir: /home/claude/chess_coach/sync_in`)
   und `get` fuer `meta/stand` (gleicher out_dir). Dann `python3 sync.py import sync_in`. Ergebnis: progress.json und drills.json.
6. Neue Partien, wenn Q "Analyse" sagt: `python3 analyze.py --fetch` (pusht request.txt, die GitHub Action holt JETZT alle neuen Partien von chess.com nach `inbox/`, analyze.py wartet auf die Rueckmeldung und analysiert alles Neue; etwa 20 Sekunden plus 10 bis 30 Sekunden je Partie). Je neuer Partie `python3 drill.py add games/<report>.json`. Kommt "Keine neue Partie", obwohl Q gerade gespielt hat: chess.com hat das Archiv noch nicht aktualisiert, in ein paar Minuten nochmal `--fetch`. Rueckfall ohne Schreibrecht: `python3 analyze.py --pull` (liest nur, was schon in `inbox/alle.pgn` liegt). Notweg: Q haengt eine PGN an, `python3 analyze.py <datei>`.
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
* `fetch_chesscom.py`: laeuft NICHT hier, sondern in der GitHub Action `.github/workflows/fetch.yml` (Ausloeser: Push auf `request.txt`, also `--fetch`; schreibt `inbox/` und die Marke `inbox/.last_run.txt`). Nur Standardbibliothek, keine Geheimnisse im Repo.

## Warum so
Aus der Claude Umgebung sind nur GitHub und Paketquellen erreichbar (geprueft 16.10.2026: api.chess.com, ntfy.sh, oracle.com alle 403; github.com, raw.githubusercontent.com, git gehen). Deshalb holt eine GitHub Action die Partien bei chess.com und legt sie ins Repo; der Chat stoesst sie per Push an und liest das Ergebnis per Pull. Das Schreibrecht kommt vom GitHub Connector in claude.ai, verbunden mit Qs privatem Konto `mlauberg` (nicht Gore). Der Fortschritt (Kennzahlen, Lektionsmuster, Drills, Antworten) liegt in der Artefakt Datenbank, Reports in `games/` sind Sitzungsware.

Geprueft 17.10.2026 00:00 aus dem Chat: `--fetch` bis zur Rueckmeldung der Action 18 Sekunden.

## Stand 16.10.2026, 23:30
* Rating nach Partie 7: 612 (Start 480 am 14.10.). 7 Partien, alle Rapid 10+0, mit Uhr.
* Stufe 1 (Captures). Letzte 7: haengen gelassen 0,86 je Partie, gratis genommen 89 %, Gegnerpatzer genutzt 45 %, Koenig in 4 von 7 nach Zug 12 in der Mitte, Blunder unter 5 Sekunden 5 von 26. Konzept faellig: Figur haengen lassen, nicht gerettet, Koenigssicherheit (eine pro Woche).
* Drill Pool: 10 Aufgaben, 4 Antworten bisher (alle richtig), Faelligkeiten werden aus dem Antwortlog berechnet.
* Datenbank: 7 Partien, 10 Drills, 4 Antworten, meta/stand (stufe 1).
* Die Seite "Road to 1000" (Adresse oben) zeigt den Bauern auf der Linie 450 bis 1000, drei Zahlen, Kurve, Partienbuch und Drills, live aus der Datenbank.
