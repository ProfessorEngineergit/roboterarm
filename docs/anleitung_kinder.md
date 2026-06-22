# 🤖 Dein Roboterarm — los geht's!

Diese Anleitung bringt dich in **5 Schritten** vom Laptop zum Arm, der einen Ball holt.
Du brauchst nur deinen **Laptop**. Kein Kabel, keine Installation.

> An jeder Station steht eine Nummer (**1**, **2** oder **3**). Nimm **deine** Nummer für
> alles unten — im Beispiel ist es Station **1**.

---

## Schritt 1 — Mit dem Arm-WLAN verbinden 📶

1. Öffne die **WLAN-Liste** auf deinem Laptop.
2. Wähle das Netz **`Roboterarm-1`** (bei Station 2 → `Roboterarm-2`, usw.).
3. Passwort: **`roboterarm`**

✅ Geschafft, wenn dein Laptop „verbunden" zeigt. (Internet gibt's hier keins — brauchst du auch nicht.)

---

## Schritt 2 — Die Oberfläche öffnen 🌐

1. Öffne einen **Browser** (Chrome, Firefox, Safari …).
2. Tippe oben in die Adresszeile:

   ### `arm1.local:8765`

   Klappt das nicht? Dann tippe stattdessen: **`10.42.0.1:8765`**

✅ Geschafft, wenn du oben **🤖 roboterarm** und ein **Kamerabild** siehst.

---

## Schritt 3 — Den Arm bewegen ✋ (erster Erfolg!)

1. Klick oben auf den Reiter **Manuell**.
2. Zieh an den **Schiebereglern** (basis, schulter, ellbogen) — der Arm bewegt sich mit!
3. Probier die Knöpfe **🏠 Home**, **✋ Greifer auf**, **✊ Greifer zu**.

> 🎉 Wenn sich der Arm bewegt, funktioniert alles. Das ist dein erster Sieg.

⚠️ Fährt der Arm gegen sich selbst? **Home** drücken — er geht in die sichere Grundstellung zurück.

---

## Schritt 4 — Dein erstes Programm 🧑‍💻

1. Klick auf den Reiter **Code**.
2. Oben ist ein Auswahlmenü **„— Beispiel wählen —"**. Wähle **„Objekt finden & aufheben"**.
3. Leg einen **orangen Ball** vor den Arm (in die Sicht der Kamera).
4. Klick **▶ Ausführen**.

Unten im schwarzen Fenster siehst du, was der Arm „denkt". Er sucht den Ball, dreht sich
hin, greift zu und legt ihn ab. **Du hast den Ball geholt!** 🟠🦾

**Jetzt selbst ändern:** Tausch im Code `"orange"` gegen `"rot"` oder `"blau"` und führ es
nochmal aus. Was passiert?

---

## Schritt 5 — Dem Arm etwas beibringen 🧠

1. Klick auf den Reiter **KI-Studio**.
2. Tipp einen Namen ein, z.B. **`Ball`**, und klick **+ hinzufügen**. Mach das auch für **`leer`**
   (= nichts in der Hand).
3. Halte den Ball vor die Kamera und klick bei „Ball" auf **📸 ×5**. Dann nimm den Ball weg
   und klick bei „leer" auf **📸 ×5**.
4. Klick **🧠 Trainieren**.
5. Schau bei **Live-Erkennung**: Halte den Ball hin → es erscheint **Ball**. Weg → **leer**.

> Der Arm hat gerade *gelernt*, deinen Ball zu erkennen — wie ein echtes KI-Modell. 🤩

---

## 🏆 Aufgaben (such dir was aus)

- **Winker:** Lass den Arm dreimal winken (Beispiel „Winken").
- **Sortierer:** Leg roten und blauen Ball hin — Beispiel „Nach Farbe sortieren".
- **Punktlandung:** Reiter Manuell → unten **gehe_zu** mit x/y/z. Triff einen Becher!
- **Dompteur:** Bring dem Arm ein neues Objekt bei (z.B. „Stift") und lass ihn es erkennen.
- **Choreograf:** Reiter **Aufnahme & Posen** → ⏺ Start → im Manuell-Tab bewegen → ⏹ Stop →
  ▶ Wiedergabe. Der Arm spielt deine Bewegung nach!

---

## 🆘 Wenn etwas klemmt

| Problem | Das hilft |
|---|---|
| Seite lädt nicht | Stimmt das WLAN (`Roboterarm-1`)? Adresse `10.42.0.1:8765` probieren. |
| Kein Kamerabild | Kurz warten, Seite neu laden (F5). |
| Arm bewegt sich nicht | **🏠 Home** drücken. Steht der Betreuer-Dienst? Betreuer fragen. |
| Arm klemmt/brummt | Sofort **Home**. Nicht mit Gewalt ziehen. |
| Programm hängt | Reiter **Code** → **■ Stop**. |

Viel Spaß — trau dich, Sachen auszuprobieren. Kaputt machen kannst du nichts! 🚀

---

> 🧩 **Blöcke statt Code** (bunte Programmierblöcke wie in Scratch) richtet dein:e Betreuer:in
> ein — frag danach, wenn du lieber mit Blöcken baust. Es kann genau dasselbe.
