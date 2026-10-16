# Lehrplan Road to 1000 (die Didaktik hinter dem Protokoll, Stand 16.10.2026)

Dieser Plan sagt dem Coach Chat, WIE Q lernt. Das Protokoll sagt, WAS pro Partie passiert. Beides gilt zusammen.

## 1. Grundsatz: Schichten, nicht Stufen, die man hinter sich laesst
Ein 2000er haengt auch mal eine Figur. Deshalb wird keine Schicht je abgeschaltet: jede bleibt dauerhaft im Drill, in der Messung und in der Routine. Neue Schichten kommen DAZU, wenn die Zahl der vorigen steht. "Umbau bei 1000" heisst nur: das Skript bekommt dann Detektoren fuer neue Muster (Plaene, Endspiel). Alles Bestehende bleibt.

## 2. Was die Lernforschung sagt, und was davon wo im System steckt
1. Abrufen schlaegt Anschauen (practice testing, hoechste Wirksamkeit laut Dunlosky et al. 2013): Drill kommt in jeder Einheit ZUERST, jede Lektion wird am naechsten Tag abgefragt, nie nur angeschaut.
2. Verteilt schlaegt geballt (distributed practice, ebenfalls hoechste Wirksamkeit): Intervalle 1, 3, 7 Tage, taeglich 15 bis 25 Minuten statt zwei Stunden am Sonntag.
3. Vorgemachtes Beispiel zuerst, dann selbst, dann ohne Hilfe (worked example effect, gilt fuer Anfaenger, verkehrt sich bei Fortgeschrittenen um): L Bilder sind das Beispiel. Beim ersten Drill derselben Stellung darf Q spicken. Ab der Wiederholung nicht mehr. Ab Stufe 3 weniger Beispiele, mehr Aufgaben.
4. Eigene Fehler vor fremden Puzzles: Drills kommen aus Qs Partien (Relevanz, Emotion, gleiche Eroeffnungen). Dazu Transfer: dasselbe Muster in fremder Stellung (Fallen Bilder, ab Stufe 2 lichess Matt in 1 und Matt in 2), weil reine Wiederholung der eigenen Stellungen Auswendiglernen statt Mustererkennung riskiert (Kritik am Woodpecker Verfahren).
5. Muster automatisieren durch Wiederholung mit Tempo (Woodpecker, de la Maza): einmal pro Woche Schnellrunde aller erledigten Drills, 10 Sekunden je Stellung, in Worten antworten.
6. Bild plus Worte, nie Notation (Q ist Seh Lerner, dual coding): jede Lektion ein Brett mit Pfeilen und ein bis drei Saetzen Alltagssprache.
7. Eine Sache zur Zeit (cognitive load): die aktuelle Schicht bestimmt Routine, Drills und Lektion 1. Mischen (interleaving) erst ab Stufe 2, dann bewusst: Drills aus Stufe 1 und 2 gemischt.
8. Sofortiges Feedback: Analyse direkt nach den Partien, Loesung als Bild direkt nach der Antwort, auch wenn sie richtig war.
9. Wenig wirksam (laut derselben Forschung): nochmal lesen, markieren, zusammenfassen. Im Schach: Videos schauen, Eroeffnungen sammeln, Puzzles weit ueber dem Niveau. Erlaubt als Unterhaltung, zaehlt nicht als Training.

## 3. Was auf 500 bis 1000 die Partien entscheidet
Stichprobe aus Partien von 600 bis 1200 (ChessMathNerd, lichess): etwa 3 Blunder je Spieler und Partie, davon etwa 2 reine Figurenverluste "ohne Grund". Qs eigene 7 Partien: 5 Blunder je 40 Zuege, 0,86 mal je Partie etwas haengen gelassen, 89 % des Gratismaterials genommen, nur 45 % der Gegnerpatzer genutzt. Das heisst: Brettsicht entscheidet, nichts anderes bewegt das Rating so schnell. Eroeffnungstheorie, Endspieltheorie und Strategie kommen spaeter dran, nicht weil sie unwichtig waeren, sondern weil sie jetzt pro Stunde Training weniger Punkte bringen.

## 4. Die Schichten

| Schicht | Routine im Spiel | Drillquelle | Kennzahl (analyze.py --progress) | naechste Schicht frei, wenn |
|---|---|---|---|---|
| 0 Rahmen (laeuft immer mit) | festes Repertoire (Bilder A bis F), Rochade bis Zug 10, nach Zug 3 nie unter 5 Sekunden ziehen | Konzeptkarten Koenigssicherheit und Zeit | Rochadezug, Koenig nach Zug 12 in der Mitte (Roch! in der Tabelle), Blunder unter 5 Sekunden, Median Sekunden je Zug | immer aktiv |
| 1 Captures | drei Blicke: kann seine gezogene Figur etwas schlagen, kann er meine Figur auf dem neuen Feld schlagen, kann ich gratis schlagen | eigene Partien: Figur haengen lassen, nicht gerettet, gratis liegen gelassen | haengen gelassen je Partie, gratis genommen % | ueber 10 Partien: haengen < 1,0 UND gratis >= 90 % |
| 2 Checks | welche Schachs hat er, welche habe ich; Mattbilder: Grundreihe, Batterie auf f7, Legal, Ersticktes Matt | eigene Partien (Matt uebersehen, Matt zugelassen, Schach mit Gewinn) plus Fallen 01, 05, 06 plus lichess Matt in 1 und 2 | Matt uebersehen oder zugelassen je Partie | ueber 10 Partien unter 0,3 je Partie, Stufe 1 Zahlen halten |
| 3 Attacks | Gabel, Fesselung, Abzug, Ueberlastung: zwei Dinge auf einmal | eigene Partien (Gabel zugelassen oder verpasst) plus Fallen 03 plus Steps Method Stufe 2 Themen | Gabel zugelassen, Gabel genutzt | ueber 10 Partien Gabel zugelassen < 0,5, Stufe 1 und 2 Zahlen halten |
| 4 Plaene (etwa ab 1000) | Entwicklung, Zentrum, Koenigssicherheit, Endspiel Koenig und Bauer, Turm gegen Koenig | kommt, wenn es so weit ist (Detektoren im Skript ergaenzen) | kommt | kommt |

Die Schichten 1 bis 3 entsprechen den ersten Stufen der Stappenmethode (Brunia, van Wijgerden; Stufe 2 dort: Doppelangriff, Fesselung, Abzugsangriff, Matt in 2, Mattsetzen mit dem Turm, Verteidigen gegen Matt). Das ist das im Vereinsschach erprobte Anfaenger Curriculum, nur auf Q zugeschnitten und mit seinen eigenen Partien als Material.

## 5. Die Tageseinheit (15 bis 25 Minuten, taeglich schlaegt einmal pro Woche lang)
1. Drill zuerst (5 Minuten): `drill.py quiz`, 3 bis 5 faellige Aufgaben. Q antwortet in Worten, Coach vergleicht mit den akzeptierten Zuegen, Loesung als Bild, `reveal --ok` oder `--fail`.
2. Beispiele anschauen (3 Minuten): L1, L2, F1, F2 der letzten Partie(n). Kein Vortrag, Bilder und ein paar Saetze Ton.
3. Spielen: 1 bis 3 Rapid Partien mit der Routine der aktuellen Schicht. Nach jeder Partie 10 Sekunden ehrlich: drei Blicke gemacht, ja oder nein.
4. "Analyse": `analyze.py --fetch`, Lektionen und Funde kommen als Bilder, Drills werden ergaenzt, eine Zeile Trend.

Woechentlich: Schnellrunde (`drill.py speed`): alle erledigten Aufgaben, 10 Sekunden je Stellung, ohne Spicken.
Alle 10 Partien: Schichtpruefung mit `analyze.py --progress`. Steht die Zahl, wird STUFE in analyze.py erhoeht und `drill.py prune` laeuft. Steht sie nicht, aendert sich nichts, ausser dass die Drills der Schicht weitergehen.
Alle 20 Partien: welche Massnahme hat die Zahlen bewegt, was nicht, Rest streichen.

## 5a. Theorie: wann und wie
Theorie kommt nicht als Vortrag, sondern als Konzeptkarte, wenn ein Muster sich wiederholt (3 von 10 Partien) oder Q fragt. Jede Karte beantwortet vier Fragen: Was ist das. Woran erkenne ich es am Bild. Was tue ich. Wann ignoriere ich es. Dazu drei eigene Stellungen und sofort Quiz. So wird aus "du hast 9 mal die Koenigssicherheit missachtet" ein Blick, den Q am Brett ausfuehren kann. Karten stehen in `KONZEPTE.md`, neue kommen dazu, wenn das Skript ein neues Muster misst.

## 6. Rolle des Coach Chats
Der Coach fuehrt die Tageseinheit in dieser Reihenfolge, haelt die Schicht, haelt den Ton (hart, fair, Spass), erfindet keine Fakten (Protokoll Abschnitt 1), schlaegt vor und Q entscheidet. Der Coach gibt keine Vortraege, keine neuen Eroeffnungen, keine Theorie und kein "mehr", solange die Zahlen nicht stehen. Wenn Q eine andere Stellung fuer lehrreicher haelt als die gewaehlte: bauen, nicht diskutieren.

## 7. Woran Fortschritt gemessen wird, in dieser Reihenfolge
1. Rapid Rating auf chess.com (die Wahrheit).
2. Kennzahlen der Schichten aus `--progress` (sagen, WARUM das Rating sich bewegt oder nicht).
3. Drill Trefferquote (mit Vorsicht: Treffer auf eigenen Stellungen beweisen noch keinen Transfer, deshalb die Schnellrunde und die fremden Stellungen).
