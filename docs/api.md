# API-Referenz (`roboterarm`)

```python
from roboterarm import Arm
arm = Arm()
```

## Bewegung
| Methode | Wirkung |
|---|---|
| `arm.home()` | Grundstellung |
| `arm.basis(w)` / `schulter(w)` / `ellbogen(w)` | Gelenk auf Winkel (Grad) |
| `arm.bewege(name, w, speed=None)` | beliebiges Gelenk, optional Tempo |
| `arm.greifer.auf()` / `arm.greifer.zu()` / `arm.greifer.setze(w)` | Greifer |
| `arm.tempo(grad_pro_schritt)` | Geschwindigkeit |
| `arm.winkel(name)` / `arm.basis_winkel()` / `arm.alle_winkel()` | aktuelle Winkel |
| `arm.gehe_zu(x, y, z)` | inverse Kinematik (mm) -> Gelenkwinkel |

## Erkennung (Farbe **oder** gelernte Klasse)
| Methode | Wirkung |
|---|---|
| `arm.sieht(ziel)` | `True/False` — `ziel` ist Farbe (`"rot"`, …) oder ML-Klasse |
| `arm.finde(ziel)` | `{x, y, groesse, bbox}` (x/y in [-1,1]) oder `None` |
| `arm.finde_alle(ziel)` | Liste aller Treffer |
| `arm.erkenne()` | `{label, confidence, proba}` des ML-Modells |

`ziel` kann auch ein eigener HSV-Bereich sein: `arm.finde([(0,100,100),(10,255,255)])`.
Farben: `rot orange gelb gruen cyan blau violett pink weiss schwarz` (+ Synonyme, + eigene in der Config).

## Verhalten
| Methode | Wirkung |
|---|---|
| `arm.suche(ziel)` | dreht die Basis, bis `ziel` sichtbar |
| `arm.zentriere_auf(ziel)` | Proportionalregelung, bis `ziel` mittig |
| `arm.hole(ziel)` | suchen → zentrieren → aufheben → ablegen |
| `arm.sortiere({ziel: basiswinkel, ...})` | Objekte in Ablagen sortieren |
| `arm.aufheben()` / `arm.ablegen()` | feste Greif-/Ablege-Sequenz |

## Maschinelles Lernen
| Methode | Wirkung |
|---|---|
| `arm.lerne(label, anzahl=15)` | Bilder aufnehmen + trainieren |
| `arm.modell.aufnehmen(label, frame)` | einzelnes Beispiel |
| `arm.modell.trainiere()` | trainieren |
| `arm.modell.bewerte()` | `{genauigkeit, confusion, …}` |
| `arm.modell.speichere(ordner)` / `Modell.lade(ordner)` | Persistenz |

Extraktor/Klassifikator wählbar: `Modell(extractor=…, klassifikator=KNN()|NaechsterCentroid()|LogReg())`.

## Posen & Aufnahme
| Methode | Wirkung |
|---|---|
| `arm.pose_speichern(name)` / `arm.pose_anfahren(name)` / `arm.posen()` | benannte Posen |
| `arm.aufnahme_start()` / `arm.aufnahme_stop()` / `arm.wiedergabe(schritte)` | Bewegung aufnehmen/abspielen |

## Projekte
```python
from roboterarm import Projekt
p = Projekt("klasse5a")
p.programm_speichern("mein_prog", code); p.programme()
p.pose_speichern("gruss", arm.alle_winkel())
```

## Verhalten-Modul
```python
from roboterarm.verhalten import winken, tanz, pick_and_place, bewache, aufraeumen
```
