# 🤖 Dein Roboterarm — los geht's!

Diese Anleitung bringt dich vom Laptop zum Arm, der sich bewegt — Stufe für Stufe,
vom einfachen Schieberegler bis zu echtem Python. Du brauchst nur deinen **Laptop**.

> An jeder Station steht eine Nummer (**1**, **2** oder **3**). Nimm **deine** Nummer für
> alles unten — im Beispiel ist es Station **1**.

---

## Schritt 1 — Mit dem Arm-WLAN verbinden 📶

1. Öffne die **WLAN-Liste** auf deinem Laptop.
2. Wähle das Netz **`Roboterarm-01`** (bei Station 2 → `Roboterarm-02`, usw.).
3. Passwort: fragt eure:n Betreuer:in.

✅ Geschafft, wenn dein Laptop „verbunden" zeigt. (Internet gibt's hier keins — brauchst du auch nicht.)

---

## Schritt 2 — Die Oberfläche öffnen 🌐

1. Öffne einen **Browser** (Chrome, Firefox, Safari …).
2. Tippe oben in die Adresszeile:

   ### `10.42.0.1:8765`

   Klappt auch: **`roboterarm-01.local:8765`**

✅ Geschafft, wenn du oben **🤖 roboterarm** und vier Reiter siehst:
**🎚 Regler · 🧩 Eigene Blöcke · 🐱 Scratch · 🐍 Python**.

---

## ⛔ Das Wichtigste zuerst: der NOT-AUS

Oben rechts ist immer ein großer roter Knopf **■ NOT-AUS**.
**Ein Klick stoppt sofort alles** — egal in welchem Reiter du bist.

> Wenn der Arm komisch fährt, klemmt oder brummt: **NOT-AUS drücken.** Danach einfach
> einen Regler bewegen oder **🏠 Grundstellung** klicken — schon geht's weiter.

---

## Stufe 1 — 🎚 Regler: den Arm direkt bewegen (erster Erfolg!)

1. Reiter **🎚 Regler**.
2. Zieh an den **Schiebereglern** (basis, schulter, ellbogen, greifer) — der Arm bewegt sich mit!
3. Probier die Knöpfe **🏠 Grundstellung**, **✋ Greifer auf**, **✊ Greifer zu**.
4. **Tempo** regelt, wie schnell er fährt.

> 🎉 Wenn sich der Arm bewegt, funktioniert alles. Das ist dein erster Sieg.

---

## Stufe 2 — 🧩 Eigene Blöcke: ein Programm zusammenklicken

1. Reiter **🧩 Eigene Blöcke**.
2. Links sind **Bausteine**. Klick sie an — sie wandern rechts in **Mein Programm**.
   Zum Beispiel: *Basis auf 140°* → *✊ Greifer zu* → *⏱ warte 1 s* → *🏠 Grundstellung*.
3. Bei manchen Bausteinen kannst du die **Zahl ändern** (z.B. den Winkel).
4. Mit **▲ ▼** umsortieren, mit **✕** löschen.
5. Unten **„Wiederhole alles … ×"** einstellen und auf **▶ Start** klicken.

> Der Arm arbeitet deine Bausteine von oben nach unten ab. Der gerade laufende
> Baustein leuchtet gelb. **■ Stop** hält sofort an.

---

## Stufe 3 — 🐱 Scratch: Blöcke ziehen wie im echten Scratch

1. Reiter **🐱 Scratch**.
2. Unten links bei den **Erweiterungen** ist **„Roboterarm"** mit fertigen Blöcken
   (*Grundstellung*, *Basis auf … Grad*, *Greifer …*, *gehe zu x y z*).
3. Zieh sie in dein Skript, häng sie an einen **grünen Fahne**-Block und klick die Fahne.

> Falls der Reiter sagt „noch nicht installiert", richtet das dein:e Betreuer:in einmal ein.

---

## Stufe 4 — 🐍 Python: für Mutige

1. Reiter **🐍 Python**.
2. Wähl oben ein **Beispiel** (z.B. „Winken") — oder schreib selbst.
3. **▶ Ausführen.** Unten im schwarzen Fenster siehst du die Ausgabe.

Mini-Befehle zum Ausprobieren:
```python
from roboterarm import Arm
arm = Arm()
arm.home()
arm.basis(120)
arm.greifer.zu()
```

---

## 🏆 Aufgaben (such dir was aus)

- **Winker:** Lass den Arm dreimal winken — als Blöcke *oder* mit dem Python-Beispiel „Winken".
- **Choreograf:** Bau in **Eigene Blöcke** eine Bewegungsfolge mit *warte*-Bausteinen dazwischen.
- **Punktlandung:** Reiter **Regler** → unten **gehe zu** mit x/y/z. Triff einen Becher!
- **Umsteiger:** Bau dieselbe Bewegung einmal als **Blöcke** und einmal in **Scratch**.
- **Tüftler:** Schreib in **Python** eine Schleife, die den Arm 5-mal hin- und herfahren lässt.

---

## 🆘 Wenn etwas klemmt

| Problem | Das hilft |
|---|---|
| Seite lädt nicht | Stimmt das WLAN (`Roboterarm-01`)? Adresse `10.42.0.1:8765` probieren. |
| Arm bewegt sich nicht | **🏠 Grundstellung** klicken. Steht der Betreuer-Dienst? Betreuer fragen. |
| Arm klemmt/brummt | Sofort **■ NOT-AUS**. Nicht mit Gewalt ziehen. |
| Programm/Code hängt | **■ NOT-AUS** oben rechts — stoppt auch laufenden Code. |
| Scratch-Reiter leer | „noch nicht installiert" → Betreuer richtet TurboWarp einmal ein. |

Viel Spaß — trau dich, Sachen auszuprobieren. Kaputt machen kannst du nichts! 🚀
