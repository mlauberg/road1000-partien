# Road to 1000, Neustart in einem neuen Chat (Stand 17.10.2026, 00:30)

Q schreibt "Road to 1000" oder "Analyse". Claude macht in dieser Reihenfolge, ohne Rueckfragen:

1. Repo: `mlauberg/road1000-partien` haengt an der Sitzung (Q waehlt es beim Start aus; sonst add_repo mit Schreibrecht, GitHub Konto `mlauberg`). Klon: `/home/claude/road1000-partien`, dort arbeiten. Pruefung: `git -C /home/claude/road1000-partien pull -q --rebase origin main && echo ok`.
2. Stockfish 17.1 (80 MB, liegt nie im Repo), drei Befehle im Klon:
   `curl -sSL -o /home/claude/sf.tar https://github.com/official-stockfish/Stockfish/releases/download/sf_17.1/stockfish-ubuntu-x86-64-avx2.tar`
   `mkdir -p engine && tar xf /home/claude/sf.tar -C engine --strip-components=1 stockfish/stockfish-ubuntu-x86-64-avx2 && mv engine/stockfish-ubuntu-x86-64-avx2 engine/stockfish && chmod +x engine/stockfish`
   `printf "uci\nquit\n" | engine/stockfish | head -1` muss "Stockfish 17.1" sagen.
3. `pip install --break-system-packages cairosvg`. Die chess Bibliothek liegt als Ordner `chess/` bei (pip chess scheitert in der Umgebung).
4. `COACH_PROTOCOL.md`, `LEHRPLAN.md`, `KONZEPTE.md` komplett lesen: Regeln, Lernmethode, Theoriekarten.
5. Stand laden. Fortschritt und Drills leben in der Datenbank des Artefakts "Road to 1000" (Adresse unten). Werkzeug ArtifactData, vier Aufrufe:
   `list` fuer `partien`, `drills`, `drill_log` (je `query: {"limit": 1000}`, `out_dir: /home/claude/road1000-partien/sync_in`) und `get` fuer `meta/stand` (gleicher out_dir).
   Dann `python3 sync.py import sync_in`. Ergebnis: progress.json, drills.json, und die Stufe laut Datenbank (muss zu STUFE in analyze.py passen).
6. "Analyse": `python3 analyze.py --fetch`. Pusht request.txt, die GitHub Action holt JETZT alle neuen Partien von chess.com nach `inbox/`, analyze.py wartet auf die Marke und analysiert alles Neue (etwa 20 Sekunden plus 10 bis 30 Sekunden je Partie). Je neuer Partie `python3 drill.py add games/<report>.json`.
   "Keine neue Partie" direkt nach dem Spielen: chess.com hat das Archiv noch nicht aktualisiert, ein paar Minuten spaeter nochmal `--fetch`.
   Rueckfall ohne Schreibrecht: `python3 analyze.py --pull` (nur was schon in `inbox/alle.pgn` liegt). Notweg: Q haengt eine PGN an, `python3 analyze.py <datei>`.
7. Tageseinheit nach Lehrplan: Drills (`drill.py quiz`, `reveal`), Lektionsbilder L1, L2, F1, F2 je Partie, eine Zeile Trend (`analyze.py --progress`).
8. Stand sichern, nach jedem Drill Block und am Ende: `python3 sync.py export sync_out`, dann die gedruckten Eintraege mit ArtifactData `batch` schreiben (bis 50 je Aufruf, nur neue Dokumente, kein if_version). Meldet export einen Stufenwechsel: `meta/stand` mit `get` lesen, mit `set` plus `if_version` auf die neue Stufe setzen. Die Seite "Road to 1000" zeigt den Stand sofort.

Derselbe Chat an einem neuen Tag: Q schreibt nur "Analyse". Claude macht dann `git pull -q --rebase origin main`, Schritt 4 (Protokoll nochmal lesen) und Schritt 5 (Stand neu laden), danach Schritt 6. Ist die Umgebung inzwischen abgeraeumt (kein `engine/stockfish`, kein Klon), Schritte 1 bis 5 komplett.

Artefakt (Datenbank und Seite): https://claude.ai/artifact/E46EePzEV7k5vKzM8i5Bhb

## Dateien
* `analyze.py <pgn> | --fetch | --pull | --progress`: Stockfish Analyse mit 2 Engines parallel, waehlt Lektion 1 und 2 (erst aktuelle Stufe, dann Wiederholung, dann groesster Verlust), rendert L1, L2 (Lektionen, 3 Bilder, Text nur aus Engine Fakten, in Worten), F1, F2 (Funde), V1 (verpasste Chance), fuehrt progress.json. `--progress`: Trend, Kennzahlen, Stufenfreigabe, faellige Konzepte. STUFE steht oben in analyze.py.
* `drill.py add | quiz | reveal | warum | stats | prune | speed`: Drill Pool zur aktuellen Stufe, Wiederholung nach 3 und 7 Tagen, Loesungen in Worten, `warum <id> <Zug>` nach jeder falschen Antwort (vier Bilder: dein Zug, seine Antwort, Folge mit Material, dasselbe nach dem besten Zug), woechentliche Schnellrunde.
* `sync.py import | export`: Stand aus der Artefakt Datenbank laden, neue Dokumente dorthin vorbereiten (nur Anlegen, nie Aendern).
* `show.py`: Bilderfolgen (storyboard), Einzelbretter (render), Zuege in Worten (move_words), Pfeilpruefung, FAKT Zeilen je Frame.
* `check.py line | fen | move | hang`: Faktencheck fuer alles, was Claude frei ueber eine Stellung sagen will.
* `bilder.py`: Repertoire A bis F, Fallen 01 bis 06, Lektion Laeufer eingesperrt (30 Sekunden, nur bauen, wenn Q eines sehen will).
* `fetch_chesscom.py` und `.github/workflows/fetch.yml`: laufen bei GitHub, nicht im Chat (von hier ist api.chess.com nicht erreichbar). Ausloeser ist der Push auf `request.txt` durch `--fetch`; Ergebnis landet in `inbox/`, die Marke `inbox/.last_run.txt` meldet den Lauf, auch wenn chess.com nicht antwortet.
* `seite.html`: Quelle der Fortschrittsseite. Aendern: erst Artifact `read` mit der Adresse oben (Pflicht vor dem Veroeffentlichen aus einem anderen Chat), dann `seite.html` bearbeiten, mit Artifact `publish` (`file_path` seite.html, `url` die Adresse oben, ohne `capabilities`, die Datenbank bleibt) veroeffentlichen, committen. Die Seite liest die Sammlungen `partien`, `drills`, `drill_log`, `meta/stand` live.
* Texte: `COACH_PROTOCOL.md` (Regeln), `LEHRPLAN.md` (Methode), `KONZEPTE.md` (Theoriekarten), dieser Neustart.
* Nicht im Repo (Sitzungsware, .gitignore): `engine/`, `games/`, `drills/`, `*.png`, `progress.json`, `drills.json`, `sync_in/`, `sync_out/`.

## Warum so
Aus der Claude Umgebung sind nur GitHub und Paketquellen erreichbar (geprueft 16.10.2026: api.chess.com 403, github.com und git gehen). Deshalb holt eine GitHub Action die Partien bei chess.com und legt sie ins Repo; der Chat stoesst sie per Push an und liest das Ergebnis per Pull. Das Schreibrecht kommt vom GitHub Connector in claude.ai, verbunden mit Qs privatem Konto `mlauberg`. Der Fortschritt liegt in der Artefakt Datenbank (lesen und schreiben ohne Connector), Reports in `games/` sind Sitzungsware.
Geprueft 17.10.2026 in einem frischen Klon, Schritte 1 bis 8 wortwoertlich: Engine Download 10 Sekunden, Import 7 Partien und 10 Drills, `--fetch` bis zur Rueckmeldung 13 bis 18 Sekunden, Quiz, Reveal, Export.

## Stand 17.10.2026, 00:30
* Rating nach Partie 7: 612 (Start 480 am 14.10.). 7 Partien, alle Rapid 10+0, mit Uhr.
* Stufe 1 (Captures). Letzte 7: haengen gelassen 0,86 je Partie, gratis genommen 89 %, Gegnerpatzer genutzt 45 %, Koenig in 4 von 7 nach Zug 12 in der Mitte, Blunder unter 5 Sekunden 5 von 26. Konzept faellig: Figur haengen lassen, nicht gerettet, Koenigssicherheit (eine pro Woche, Protokoll 5a).
* Drill Pool: 10 Aufgaben, 4 Antworten bisher (alle richtig). Faelligkeiten rechnet sync.py aus dem Antwortlog.
* Datenbank: 7 Partien, 10 Drills, 4 Antworten, meta/stand (stufe 1).
