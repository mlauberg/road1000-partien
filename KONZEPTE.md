# Konzeptkarten (Stand 16.10.2026)

Eine Karte wird gezogen, wenn `analyze.py --progress` "KONZEPT FAELLIG" sagt (dasselbe Muster in 3 der letzten 10 Partien) oder wenn Q nach dem Begriff fragt. Ablauf einer Konzeptlektion: 1) Karte vorlesen, Wort fuer Wort erlaubt, nichts dazu erfinden. 2) Drei eigene Stellungen von Q mit diesem Muster als Bilder (aus games/*.json, mit `show.py fen` oder `drill.py`), Q wendet die Erkennungsliste laut an. 3) Sofort Quiz: dieselben drei Stellungen ohne Pfeile, Q antwortet in Worten. Hoechstens eine Konzeptlektion pro Woche. Jede Karte hat vier Teile: Was ist das. Woran erkenne ich es am Bild. Was tue ich. Wann ignoriere ich es.

## Figur haengen lassen (Schicht 1, Blick 2)
Was: Nach meinem Zug kann er eine Figur von mir schlagen, und ich kann nicht gleichwertig zurueckschlagen.
Erkennen: Ich schaue auf die Figur, die ich gerade ziehen will, auf ihrem NEUEN Feld. Welche gegnerischen Figuren sehen dieses Feld (Linien, Diagonalen, Springerspruenge, Bauern schraeg)? Wer von mir deckt es? Zaehlen: mehr Angreifer als Verteidiger, oder der billigste Angreifer ist billiger als meine Figur, dann haengt sie.
Tun: Anderes Feld, oder erst decken, oder den Angreifer schlagen. Nie "er sieht es schon nicht".
Ignorieren: Wenn ich dafuer mehr bekomme (Matt, seine Dame, Figur fuer Figur plus Bauer), und zwar laut Rechnung, nicht laut Hoffnung.

## Angegriffene Figur nicht gerettet (Schicht 1, Blick 1)
Was: Sein letzter Zug greift eine Figur von mir an, und mein Zug kuemmert sich nicht darum.
Erkennen: Zuerst die Figur anschauen, die ER gerade gezogen hat. Welche Felder sieht sie jetzt neu? Dann die Linie, die sie freigegeben hat (hinter ihr stand vielleicht ein Turm oder Laeufer). Steht auf einem dieser Felder etwas von mir, das weniger gedeckt als angegriffen ist?
Tun: Reihenfolge: 1) Angreifer schlagen, 2) wegziehen mit Tempo (Schach oder Gegenangriff), 3) wegziehen, 4) decken (nur wenn der Angreifer gleich viel oder mehr wert ist), 5) dazwischenstellen.
Ignorieren: Wenn ich einen staerkeren Gegenangriff habe (Schach, Matt, seine Dame), und erst nach dem Blunder Check.

## Gratis Material liegen gelassen (Schicht 1, Blick 3)
Was: Eine Figur von ihm kann ich schlagen, ohne dass er gleichwertig zurueckschlaegt, und ich tue es nicht.
Erkennen: Vor jedem Zug alle seine Figuren abklopfen: Welche sieht eine Figur von mir? Ist sie ungedeckt, oder ist mein Angreifer billiger als sie?
Tun: Nehmen. Erst nehmen, dann planen. Ausnahme nur bei Matt gegen mich im naechsten Zug.
Ignorieren: Wenn das Schlagen meine Figur auf ein Feld bringt, wo sie dann selbst haengt (Blick 2 danach), oder wenn es ein Koeder ist: ungedeckte Figur plus seine Dame oder sein Springer stehen so, dass nach dem Schlagen eine Gabel oder ein Schach kommt.

## Matt uebersehen und Matt zugelassen (Schicht 2, Checks)
Was: Ich habe Matt in 1 oder 2 und spiele etwas anderes, oder ich lasse ihm Matt in 1 zu.
Erkennen: Vor jedem Zug beide Koenige: Wie viele Fluchtfelder hat sein Koenig, wie viele meiner? Null oder eins Fluchtfelder heisst Alarm. Dann: Welche Schachs gibt es (fuer mich und fuer ihn)? Jedes Schach pruefen: Kann der Koenig weg, kann die Schachfigur geschlagen werden, kann etwas dazwischen? Dreimal nein heisst Matt.
Tun: Wenn ich Matt habe, spielen, egal was sonst auf dem Brett ist. Wenn er Matt droht, zuerst Luft fuer den Koenig oder die Drohung beseitigen, alles andere wartet.
Ignorieren: Nie. Schachs werden immer zuerst geprueft, auch wenn sie nutzlos aussehen.

## Gabel (Schicht 3, Attacks)
Was: Eine Figur greift zwei Dinge gleichzeitig an, nur eines kann gerettet werden. Springer gegen Dame und Koenig, Bauer gegen zwei Figuren, Dame mit Schach gegen einen ungedeckten Turm.
Erkennen: Fuer ihn: Wo kann sein Springer in einem Zug hin, und was sieht er von dort? Stehen mein Koenig und meine Dame, oder zwei ungedeckte Figuren, auf Feldern, die ein Springer gleichzeitig erreicht (gleiche Farbe, ein Springersprung auseinander)? Fuer mich: dieselbe Frage mit meinen Figuren. Bauerngabel: zwei meiner Figuren nebeneinander auf einer Reihe, sein Bauer eine Reihe davor.
Tun: Vorher: Dame und Koenig nicht auf Springerfelder stellen, Figuren nicht paarweise vor Bauern parken. Nachher: die wertvollere Figur retten, am besten mit Schach oder Gegenangriff.
Ignorieren: Wenn die gabelnde Figur sofort geschlagen werden kann (Blick 3), ist die Gabel keine.

## Koenigssicherheit (Schicht 0, laeuft immer mit)
Was: Mein Koenig ist sicher, wenn er rochiert ist, drei Bauern vor ihm stehen, die Linien zu ihm geschlossen sind und er mehr Verteidiger als Angreifer in seiner Naehe hat. In Qs Partien 1 bis 7 stand der Koenig in 4 von 7 Partien nach Zug 12 noch in der Mitte, waehrend die gegnerische Dame lebte. In Partie 1 war das das Matt auf e1.
Erkennen, vier Blicke auf das Bild: 1) Steht mein Koenig noch auf e1 oder e8 und es ist Zug 8 oder spaeter? 2) Ist die Linie oder Diagonale vor ihm offen (kein eigener Bauer davor, e Linie oder d Linie ohne Bauern)? 3) Wie viele seiner Figuren zeigen in Richtung meines Koenigs (Dame, Tuerme auf offenen Linien, Laeufer auf der langen Diagonale, Springer auf f5 oder d5 Hoehe)? Drei oder mehr heisst Alarm. 4) Stehen die drei Bauern vor dem rochierten Koenig noch, oder habe ich einen gezogen (h3, g3, f3 schaffen Loecher)?
Tun: Rochade bis Zug 10, egal was. Vor der Rochade keine Bauern vor dem Koenig ziehen. Keine Linie vor dem eigenen Koenig oeffnen (nicht mit e oder d Bauer schlagen, wenn dann die Linie zum Koenig frei wird). Wenn er drei Figuren auf meinen Koenig richtet: eine Figur zurueck zur Verteidigung, Damen tauschen, oder Linien schliessen, BEVOR der Angriff da ist. Die Entscheidung, die eine Engine in 90 % der Faelle trifft: Koenig erst in Sicherheit, dann angreifen.
Ignorieren: Im Endspiel ohne Damen ist der Koenig eine Kampffigur, dann in die Mitte mit ihm.

## Zeit (Schicht 0, laeuft immer mit)
Was: Ein Zug unter 5 Sekunden nach Zug 3 ist kein Zug, sondern ein Reflex. Drei Blicke dauern 5 bis 10 Sekunden.
Erkennen: Die Uhr im Report: Median Sekunden je Zug und "Blunder unter 5 Sekunden".
Tun: Nach seinem Zug zuerst seine gezogene Figur anschauen, dann erst an den eigenen Zug denken. Bei 10 Minuten Rapid sind 5 Sekunden je Zug 40 Zuege lang bezahlbar.
Ignorieren: Zwangszuege (einzige Rueckeroberung, einziges Fluchtfeld) duerfen schnell sein.
