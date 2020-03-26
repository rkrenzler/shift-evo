# Planoptimierung bei #WirVsVirus Hackaton

Ruslan Krenzler 26.03.2020


## Problembeschreibung
Wir möchten Schichten für das Pflegepersonal zuweisen. Dabei müssen wir Regeln für Arbeitszeiten anhalten, Teams effizient halten, Risiko für Infektion berücksichtigen und Wünsche der Mitarbeiter mitberücksichtigen. Am Ende möchten wir die Schichten möglichst voll kriegen.

## Mathematische Ergebnisse soweit:
Ein Priorisierungalgorithmus, ein evolutionärer Algorithmus, Mixed Integer Programming, ein einfaches Wahrscheinlichkeitsmodel für Infektionsrisiko.

Sie haben folgende Eigenschaften (Vorteile sind mit "+", Nachteile sind mit "-" markiert):

* Priorisierung: + extrem schnell, Lösungqualität vermuttlich 2/5.
* Mixed Integer Programming: + Lösungqualität 5/5 wenn es funktioniert, - langsam, - nicht flexibel, - sehr langsam zu entwickeln, - viele kommerzielle Bibliotheken sind teuer.
* Evolutionärer Algorithmus: + sehr flexibel, + schnell zu entwickeln, Lösungqualität 3/5,  - sehr langsam.
* Alles manuell machen: + sehr flexibel, - extrem langsam, - teuer, - nicht skalierbar, -Lösungsqualität vermutlich 1/5.

## Wichtige TODOs

Wir müssen Regeln und Wünsche die Personalplanung in Zahlen, Pseudo-Code und Formeln beschreiben. Nur so können wir in Zahlen und Formeln Ergebnisse produzieren die eine Maschine, ein Informatiker oder eine Mathematikerin verstehen wird. Erst ab diesem Punkt können viele Forscher an dem Problem arbeiten.

Wir brauche eine sehr gute Dokumentation. Ohne Dokumentation haben wir keine Skalierung, keine Zusammenarbeit und keine Robustheit. In diesem Projekt werden viele Entwickler ausfallen.

## Technische TODOs

Wir brauchen eine Schnittstelle zwischen IT und dem Optiemerer.

Wir brauchen eine Variante von Software, die auch ohne Internet funktioniert.


## Neue mathematische Ideen:

Algorithmen mischen:

 1. Ein evolutionärer Algorithmus erstellt einen langfristigen Plan. (Etwa: eine Stunde lang einen Monatsplan berechnen). Dann fließen diese  Ergebnisse im Form einer Empfehlung in den Priorisierungalgorithmus.
 
 2. Der Mensch nutzt am nächsten den Tag Priorisierungsalgorithmus, um Schichten für den nachfolgenden Tag zu planen und den heutigen Plan zu korrigieren.

Die weniger flexiblen MIP-Algorithmen können wir zur Erstellung von Anfangslösungen nutzen. Diese Anfangslösungen jagen wir dann durch den evolutionären Algorithmus.